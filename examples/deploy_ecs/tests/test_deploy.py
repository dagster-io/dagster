# pylint: disable=redefined-outer-name,unused-argument
import os
import shutil
import subprocess

import pytest
import yaml

from dagster import file_relative_path

pytest_plugins = ["dagster_test.fixtures"]


@pytest.fixture
def docker_context(test_id, monkeypatch, tmpdir):
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
    subprocess.call(["docker", "context", "create", "ecs", "--local-simulation", test_id])

    yield test_id

    subprocess.call(["docker", "context", "rm", test_id])


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
            shutil.copytree(source, modules / requirement, ignore=shutil.ignore_patterns(".tox"))
            overrides.append(f"./modules/{requirement}\n")

        with open(path, "w", encoding="utf8") as f:
            f.writelines(overrides)

    return modules


@pytest.fixture
def overridden_dockerfile(source_code):
    # Override Dockerfile to copy our source code into the container
    with open("Dockerfile", "r", encoding="utf8") as f:
        dockerfile = f.readlines()
        # Copy the files in directly after we set the WORKDIR
        index = dockerfile.index("WORKDIR $DAGSTER_HOME\n") + 1
        copy = ["RUN mkdir -p $DAGSTER_HOME/modules\n", "COPY modules $DAGSTER_HOME/modules\n"]
        dockerfile = dockerfile[:index] + copy + dockerfile[index:]
    with open("Dockerfile", "w", encoding="utf8") as f:
        f.writelines(dockerfile)


@pytest.fixture
def overridden_dagster_yaml(reference_deployment):
    # Override dagster.yaml to use DefaultRunLauncher; EcsRunLauncher can only
    # run on a real ECS cluster whereas DefaultRunLauncher can successfully run
    # end-to-end on a local ECS simulation. This is because the local ECS
    # simulation doesn't mock out the ECS API in its entirety.
    with open("dagster.yaml", "r", encoding="utf8") as f:
        dagster_yaml = yaml.safe_load(f)
        dagster_yaml["run_launcher"] = {
            "module": "dagster.core.launcher",
            "class": "DefaultRunLauncher",
        }
    with open("dagster.yaml", "w", encoding="utf8") as f:
        f.write(yaml.safe_dump(dagster_yaml))


@pytest.fixture
def docker_compose(
    source_code,
    overridden_dockerfile,
    overridden_dagster_yaml,
    docker_context,
    docker_compose_cm,
    monkeypatch,
    test_id,
):
    # docker-compose.yml expects this envvar to be set so it can tag images
    monkeypatch.setenv("REGISTRY_URL", "test")
    with docker_compose_cm(docker_context=docker_context) as docker_compose:
        yield docker_compose


def test_deploy(docker_compose, retrying_requests):
    assert retrying_requests.get(f'http://{docker_compose["dagit"]}:3000/dagit_info').ok
