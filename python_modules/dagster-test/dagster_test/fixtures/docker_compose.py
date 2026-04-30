import json
import logging
import os
import subprocess
from collections.abc import Mapping, Sequence
from contextlib import contextmanager

import pytest
import yaml

from dagster_test.fixtures.utils import BUILDKITE

# Hard upper bound on `docker compose up`. Set generously enough to cover cold image pulls
# on a busy CI agent, but well below pytest-timeout so we fail with diagnostics rather than
# being killed mid-syscall by the per-test timeout (which gives an unactionable traceback).
_DOCKER_COMPOSE_UP_TIMEOUT = 240

# Tear-down should be fast; if it isn't, the daemon is already wedged and we shouldn't
# block the rest of the suite trying to clean up.
_DOCKER_COMPOSE_DOWN_TIMEOUT = 90

# Bound for short-lived inspect/list/network operations.
_DOCKER_COMMAND_TIMEOUT = 60


def _docker_env() -> dict[str, str]:
    env = os.environ.copy()
    if env.get("BUILDKITE"):
        env["DOCKER_API_VERSION"] = "1.41"
    return env


def _run_docker(
    args: Sequence[str],
    *,
    timeout: float,
    env: Mapping[str, str] | None = None,
    check: bool = True,
    capture_output: bool = False,
    on_timeout_dump: Sequence[Sequence[str]] | None = None,
) -> "subprocess.CompletedProcess[bytes]":
    """Run a docker subprocess with a hard timeout.

    On TimeoutExpired, optionally invoke `on_timeout_dump` (additional docker commands
    whose output is logged) before re-raising. This is the fail-fast wrapper test
    fixtures should use for `docker` / `docker compose`, so a wedged daemon doesn't
    silently consume the per-test pytest-timeout.
    """
    run_env = dict(env) if env is not None else _docker_env()
    try:
        return subprocess.run(
            list(args),
            env=run_env,
            timeout=timeout,
            check=check,
            capture_output=capture_output,
        )
    except subprocess.TimeoutExpired:
        logging.error(
            "docker command timed out after %.0fs: %s",
            timeout,
            " ".join(str(a) for a in args),
        )
        if on_timeout_dump:
            for diag_args in on_timeout_dump:
                try:
                    diag = subprocess.run(
                        list(diag_args),
                        env=run_env,
                        timeout=_DOCKER_COMMAND_TIMEOUT,
                        check=False,
                        capture_output=True,
                    )
                    logging.error(
                        "diagnostic %s -> rc=%d\nstdout:\n%s\nstderr:\n%s",
                        " ".join(str(a) for a in diag_args),
                        diag.returncode,
                        diag.stdout.decode(errors="replace"),
                        diag.stderr.decode(errors="replace"),
                    )
                except subprocess.TimeoutExpired:
                    logging.error(
                        "diagnostic command itself timed out: %s",
                        " ".join(str(a) for a in diag_args),
                    )
        raise


@contextmanager
def docker_compose_cm(
    docker_compose_yml,
    network_name=None,
    docker_context=None,
    service=None,
    env_file=None,
    no_build: bool = False,
):
    if not network_name:
        network_name = network_name_from_yml(docker_compose_yml)

    try:
        try:
            docker_compose_up(
                docker_compose_yml, docker_context, service, env_file, no_build=no_build
            )
        except:
            dump_docker_compose_logs(docker_context, docker_compose_yml)
            raise

        if BUILDKITE:
            # When running in a container on Buildkite, we need to first connect our container
            # and our network and then yield a dict of container name to the container's
            # hostname.
            with buildkite_hostnames_cm(network_name) as hostnames:
                yield hostnames
        else:
            # When running locally, we don't need to jump through any special networking hoops;
            # just yield a dict of container name to "localhost".
            yield dict((container, "localhost") for container in list_containers())
    finally:
        docker_compose_down(docker_compose_yml, docker_context, service, env_file)


def dump_docker_compose_logs(context, docker_compose_yml):
    if context:
        compose_command = ["docker", "--context", context, "compose"]
    else:
        compose_command = ["docker", "compose"]

    compose_command += [
        "--file",
        str(docker_compose_yml),
        "logs",
    ]

    try:
        _run_docker(compose_command, timeout=_DOCKER_COMMAND_TIMEOUT, check=False)
    except subprocess.TimeoutExpired:
        logging.warning("dumping docker compose logs timed out")


@pytest.fixture(scope="module", name="docker_compose_cm")
def docker_compose_cm_fixture(test_directory):
    @contextmanager
    def _docker_compose(
        docker_compose_yml=None,
        network_name=None,
        docker_context=None,
        service=None,
        env_file=None,
        no_build: bool = False,
    ):
        if not docker_compose_yml:
            docker_compose_yml = default_docker_compose_yml(test_directory)
        with docker_compose_cm(
            docker_compose_yml, network_name, docker_context, service, env_file, no_build
        ) as hostnames:
            yield hostnames

    return _docker_compose


@pytest.fixture
def docker_compose(docker_compose_cm):
    with docker_compose_cm() as docker_compose:
        yield docker_compose


def docker_compose_up(docker_compose_yml, context, service, env_file, no_build: bool = False):
    docker_env = _docker_env()
    if context:
        compose_command = ["docker", "--context", context, "compose"]
    else:
        compose_command = ["docker", "compose"]

    if env_file:
        compose_command += ["--env-file", env_file]

    compose_command += [
        "--file",
        str(docker_compose_yml),
        "up",
        "--detach",
    ]

    if no_build:
        compose_command += ["--no-build"]

    if service:
        compose_command.append(service)

    diagnostics = [
        ["docker", "compose", "--file", str(docker_compose_yml), "ps"],
        [
            "docker",
            "compose",
            "--file",
            str(docker_compose_yml),
            "logs",
            "--no-color",
            "--tail",
            "200",
        ],
        ["docker", "ps", "--all"],
        ["docker", "info"],
    ]
    _run_docker(
        compose_command,
        env=docker_env,
        timeout=_DOCKER_COMPOSE_UP_TIMEOUT,
        on_timeout_dump=diagnostics,
    )


def _force_disconnect_external_containers(docker_compose_yml, docker_env):
    """Force-disconnect any non-compose containers still attached to compose networks.

    `docker compose down` fails if external containers (e.g. the Buildkite agent container)
    are still connected to a compose-managed network. This preemptively cleans those up so
    that `docker compose down` can remove networks without error.
    """
    network_names = network_names_from_yml(docker_compose_yml)

    # Get the list of containers managed by this compose file
    try:
        compose_result = _run_docker(
            ["docker", "compose", "--file", str(docker_compose_yml), "ps", "--format", "{{.Name}}"],
            env=docker_env,
            timeout=_DOCKER_COMMAND_TIMEOUT,
            capture_output=True,
        )
        compose_containers = set(compose_result.stdout.decode().splitlines())
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        compose_containers = set()

    for network_name in network_names:
        try:
            inspect_result = _run_docker(
                [
                    "docker",
                    "network",
                    "inspect",
                    network_name,
                    "--format",
                    "{{range .Containers}}{{.Name}} {{end}}",
                ],
                env=docker_env,
                timeout=_DOCKER_COMMAND_TIMEOUT,
                capture_output=True,
            )
            connected = inspect_result.stdout.decode().split()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue  # Network doesn't exist or already removed

        for container in connected:
            if container and container not in compose_containers:
                logging.info(
                    f"Force-disconnecting external container {container} from network {network_name}"
                )
                try:
                    _run_docker(
                        ["docker", "network", "disconnect", "--force", network_name, container],
                        env=docker_env,
                        timeout=_DOCKER_COMMAND_TIMEOUT,
                        check=False,
                    )
                except subprocess.TimeoutExpired:
                    logging.warning("Timed out disconnecting %s from %s", container, network_name)


def docker_compose_down(docker_compose_yml, context, service, env_file):
    docker_env = _docker_env()
    if context:
        compose_command = ["docker", "--context", context, "compose"]
    else:
        compose_command = ["docker", "compose"]

    if env_file:
        compose_command += ["--env-file", env_file]

    if service:
        compose_command += ["--file", str(docker_compose_yml), "down", "--volumes", service]
    else:
        _force_disconnect_external_containers(docker_compose_yml, docker_env)
        compose_command += [
            "--file",
            str(docker_compose_yml),
            "down",
            "--volumes",
            "--remove-orphans",
        ]

    try:
        result = _run_docker(
            compose_command,
            env=docker_env,
            timeout=_DOCKER_COMPOSE_DOWN_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        logging.warning("docker compose down timed out; containers may be orphaned")
        return
    if result.returncode != 0:
        logging.warning(
            "docker compose down exited with status %d",
            result.returncode,
        )


def list_containers():
    # TODO: Handle default container names: {project_name}_service_{task_number}
    result = _run_docker(
        ["docker", "ps", "--format", "{{.Names}}"],
        timeout=_DOCKER_COMMAND_TIMEOUT,
        capture_output=True,
    )
    return result.stdout.decode().splitlines()


def current_container():
    with open("/etc/hostname") as f:
        container_id = f.read().strip()
    result = _run_docker(
        ["docker", "ps", "--filter", f"id={container_id}", "--format", "{{.Names}}"],
        timeout=_DOCKER_COMMAND_TIMEOUT,
        capture_output=True,
    )
    return result.stdout.strip().decode()


def connect_container_to_network(container, network):
    # check=False so we don't fail when trying to connect a container to a network
    # that it's already connected to
    try:
        result = _run_docker(
            ["docker", "network", "connect", network, container],
            timeout=_DOCKER_COMMAND_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        logging.warning(f"Timed out connecting {container} to network {network}.")
        return
    if result.returncode == 0:
        logging.info(f"Connected {container} to network {network}.")
    else:
        logging.warning(f"Unable to connect {container} to network {network}.")


def disconnect_container_from_network(container, network):
    try:
        result = _run_docker(
            ["docker", "network", "disconnect", "--force", network, container],
            timeout=_DOCKER_COMMAND_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        logging.warning(f"Timed out disconnecting {container} from network {network}.")
        return
    if result.returncode == 0:
        logging.info(f"Disconnected {container} from network {network}.")
    else:
        logging.warning(f"Unable to disconnect {container} from network {network}.")


def hostnames(network):
    hostnames = {}
    for container in list_containers():
        result = _run_docker(
            ["docker", "inspect", container],
            timeout=_DOCKER_COMMAND_TIMEOUT,
            capture_output=True,
        )
        networking = json.loads(result.stdout)[0]["NetworkSettings"]
        hostname = networking["Networks"].get(network, {}).get("IPAddress")
        if hostname:
            hostnames[container] = hostname
    return hostnames


@contextmanager
def buildkite_hostnames_cm(network):
    container = current_container()

    try:
        connect_container_to_network(container, network)
        yield hostnames(network)

    finally:
        disconnect_container_from_network(container, network)


def default_docker_compose_yml(default_directory) -> str:
    if os.path.isfile("docker-compose.yml"):
        return os.path.join(os.getcwd(), "docker-compose.yml")
    else:
        return os.path.join(default_directory, "docker-compose.yml")


def network_names_from_yml(docker_compose_yml) -> list[str]:
    with open(docker_compose_yml) as f:
        config = yaml.safe_load(f)
    if "name" in config:
        project_name = config["name"]
    else:
        dirname = os.path.dirname(docker_compose_yml)
        project_name = os.path.basename(dirname)
    if "networks" in config:
        return [
            config["networks"][key].get("name", f"{project_name}_{key}")
            if isinstance(config["networks"][key], dict)
            else f"{project_name}_{key}"
            for key in config["networks"]
        ]
    else:
        return [f"{project_name}_default"]


def network_name_from_yml(docker_compose_yml) -> str:
    return network_names_from_yml(docker_compose_yml)[0]
