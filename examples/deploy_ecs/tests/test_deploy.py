# pylint: disable=redefined-outer-name,unused-argument
import json
import os
import shutil
import subprocess

import pytest
import requests
import yaml
from dagster import file_relative_path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@pytest.fixture
def session():
    session = requests.Session()
    session.mount("http://", HTTPAdapter(max_retries=Retry(total=7, backoff_factor=1)))
    return session


@pytest.fixture
def docker_context(testrun_uid, monkeypatch, tmpdir):
    # Docker contexts are stored in $HOME/.docker/contexts
    # Buildkite doesn't have $HOME set by default. When it's not set,
    # `docker create context` will save the context in the current directory.
    # But `docker compose` will fail if $HOME isn't set and you try to pass a
    # context.
    monkeypatch.setenv("HOME", str(tmpdir))

    # The ECS Local Simulation context expects to mount a $HOME/.aws volume
    # when you call `docker compose up`
    (tmpdir / ".aws").mkdir()

    # Use ecs --local-simulation
    # https://docs.docker.com/cloud/ecs-integration/#local-simulation
    subprocess.call(["docker", "context", "create", "ecs", "--local-simulation", testrun_uid])

    yield

    subprocess.call(["docker", "context", "rm", testrun_uid])


@pytest.fixture
def reference_deployment(tmpdir):
    destination = tmpdir / "deploy_ecs"
    # Copy the reference deployment into tmpdir
    shutil.copytree(file_relative_path(__file__, ".."), destination)

    with destination.as_cwd():
        yield destination


@pytest.fixture
def source_code(reference_deployment, tmpdir):
    # Typically, the requirements files install from pypi. For tests, we want to
    # build from source. This fixture copies any required Dagster source code
    # into tmpdir and rewrites requirements*.txt to install from the local copy.
    python_modules = file_relative_path(__file__, "../../../python_modules/")
    libraries = file_relative_path(python_modules, "libraries/")
    modules = reference_deployment / "modules"

    for path in reference_deployment.listdir():
        if not path.basename.startswith("requirements"):
            continue
        if not path.ext == ".txt":
            continue

        overrides = []
        for requirement in path.read().splitlines():
            # The source code lives in dagster/python_modules
            if requirement in os.listdir(python_modules):
                source = file_relative_path(python_modules, requirement)
            # The source code lives in dagster/python_modules/libraries
            elif requirement in os.listdir(libraries):
                source = file_relative_path(libraries, requirement)
            # It's not a dagster library; continue to install from pypi
            else:
                overrides.append(requirement + "\n")
                continue
            shutil.copytree(source, modules / requirement)
            overrides.append(f"./modules/{requirement}\n")

        with open(path, "w") as f:
            f.writelines(overrides)

    return modules


@pytest.fixture
def overridden_dockerfile(source_code):
    # Override Dockerfile to copy our source code into the container
    with open("Dockerfile", "r") as f:
        dockerfile = f.readlines()
        # Copy the files in directly after we set the WORKDIR
        index = dockerfile.index("WORKDIR $DAGSTER_HOME\n") + 1
        copy = ["RUN mkdir -p $DAGSTER_HOME/modules\n", "COPY modules $DAGSTER_HOME/modules\n"]
        dockerfile = dockerfile[:index] + copy + dockerfile[index:]
    with open("Dockerfile", "w") as f:
        f.writelines(dockerfile)


@pytest.fixture
def overridden_dagster_yaml(reference_deployment):
    # Override dagster.yaml to use DefaultRunLauncher; EcsRunLauncher can only
    # run on a real ECS cluster whereas DefaultRunLauncher can successfully run
    # end-to-end on a local ECS simulation. This is because the local ECS
    # simulation doesn't mock out the ECS API in its entirety.
    with open("dagster.yaml", "r") as f:
        dagster_yaml = yaml.safe_load(f)
        dagster_yaml["run_launcher"] = {
            "module": "dagster.core.launcher",
            "class": "DefaultRunLauncher",
        }
    with open("dagster.yaml", "w") as f:
        f.write(yaml.safe_dump(dagster_yaml))


@pytest.fixture
def docker_compose(
    source_code,
    overridden_dockerfile,
    overridden_dagster_yaml,
    docker_context,
    monkeypatch,
    testrun_uid,
):
    # docker-compose.yml expects this envvar to be set so it can tag images
    monkeypatch.setenv("REGISTRY_URL", "test")

    subprocess.call(
        [
            "docker",
            "--context",
            testrun_uid,
            "compose",
            "--project-name",
            testrun_uid,
            "up",
            "--detach",
        ]
    )

    yield

    subprocess.call(
        ["docker", "--context", testrun_uid, "compose", "--project-name", testrun_uid, "down"]
    )


@pytest.fixture
def hostnames(monkeypatch, docker_compose, testrun_uid):
    # Get a list of all running containers. We'll use this to yield a dict of
    # container name to hostname.
    containers = (
        subprocess.check_output(["docker", "ps", "--format", "{{.Names}}"]).decode().splitlines()
    )

    # When running locally, we don't need to jump through
    # any special networking hoops; we can talk to services on localhost and
    # return early.
    if not os.environ.get("BUILDKITE"):
        yield dict((container, "localhost") for container in containers)
        return

    # If we're on Buildkite, we need to do our usual Docker shennanigans:
    # https://github.com/dagster-io/dagster/blob/b16a9d78cf2fd01ca3a160ac8c04759de6c93dbd/.buildkite/dagster-buildkite/dagster_buildkite/utils.py#L71-L96
    # Only this time, do it from within our test fixture

    # Find our current container
    current_container_id = subprocess.check_output(["cat", "/etc/hostname"]).strip().decode()
    current_container = (
        subprocess.check_output(
            ["docker", "ps", "--filter", f"id={current_container_id}", "--format", "{{.Names}}"]
        )
        .strip()
        .decode()
    )

    # Find the network that our `docker compose up` command created
    network_name = (
        subprocess.check_output(
            [
                "docker",
                "network",
                "ls",
                "--filter",
                f"name={testrun_uid}",
                "--format",
                "{{.Name}}",
            ]
        )
        .strip()
        .decode()
    )

    # Connect the two
    subprocess.call(["docker", "network", "connect", network_name, current_container])

    # Map container names to hostnames
    hostnames = {}
    for container in containers:
        output = subprocess.check_output(["docker", "inspect", container])
        networking = json.loads(output)[0]["NetworkSettings"]
        hostname = networking["Networks"].get(network_name, {}).get("IPAddress")
        if hostname:
            hostnames[container] = hostname

    yield hostnames

    # Disconnect our container so that the network can be cleaned up.
    subprocess.call(["docker", "network", "disconnect", network_name, current_container])


def test_deploy(hostnames, session):
    assert session.get(f'http://{hostnames["dagit"]}:3000/dagit_info').ok
