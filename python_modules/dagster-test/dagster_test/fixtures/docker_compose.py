import json
import logging
import os
import subprocess
from contextlib import contextmanager

import pytest
import yaml

from dagster_test.fixtures.utils import BUILDKITE


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

    subprocess.run(compose_command, check=False)


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

    subprocess.check_call(compose_command)


def docker_compose_down(docker_compose_yml, context, service, env_file):
    if context:
        compose_command = ["docker", "--context", context, "compose"]
    else:
        compose_command = ["docker", "compose"]

    if env_file:
        compose_command += ["--env-file", env_file]

    if service:
        compose_command += ["--file", str(docker_compose_yml), "down", "--volumes", service]
        subprocess.check_call(compose_command)

    else:
        compose_command += [
            "--file",
            str(docker_compose_yml),
            "down",
            "--volumes",
            "--remove-orphans",
        ]
        subprocess.check_call(compose_command)


def list_containers():
    # TODO: Handle default container names: {project_name}_service_{task_number}
    return subprocess.check_output(["docker", "ps", "--format", "{{.Names}}"]).decode().splitlines()


def current_container():
    container_id = subprocess.check_output(["cat", "/etc/hostname"]).strip().decode()
    container = (
        subprocess.check_output(
            ["docker", "ps", "--filter", f"id={container_id}", "--format", "{{.Names}}"]
        )
        .strip()
        .decode()
    )
    return container


def connect_container_to_network(container, network):
    # subprocess.run instead of subprocess.check_call so we don't fail when
    # trying to connect a container to a network that it's already connected to
    try:
        subprocess.check_call(["docker", "network", "connect", network, container])
        logging.info(f"Connected {container} to network {network}.")
    except subprocess.CalledProcessError:
        logging.warning(f"Unable to connect {container} to network {network}.")


def disconnect_container_from_network(container, network):
    try:
        subprocess.check_call(["docker", "network", "disconnect", network, container])
        logging.info(f"Disconnected {container} from network {network}.")
    except subprocess.CalledProcessError:
        logging.warning(f"Unable to disconnect {container} from network {network}.")


def hostnames(network):
    hostnames = {}
    for container in list_containers():
        output = subprocess.check_output(["docker", "inspect", container])
        networking = json.loads(output)[0]["NetworkSettings"]
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


def network_name_from_yml(docker_compose_yml) -> str:
    with open(docker_compose_yml) as f:
        config = yaml.safe_load(f)
    if "name" in config:
        name = config["name"]
    else:
        dirname = os.path.dirname(docker_compose_yml)
        name = os.path.basename(dirname)
    if "networks" in config:
        network_name = next(iter(config["networks"].keys()))
    else:
        network_name = "default"

    return f"{name}_{network_name}"
