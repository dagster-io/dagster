import os
import tempfile

import pytest
from dagster import AssetExecutionContext, asset, materialize
from dagster._core.pipes.utils import (
    PipesFileContextInjector,
)
from dagster_docker.pipes import PipesDockerClient
from dagster_test.test_project import (
    IS_BUILDKITE,
    find_local_test_image,
    get_buildkite_registry_config,
    get_test_project_docker_image,
)


@pytest.mark.integration
def test_default():
    docker_image = get_test_project_docker_image()

    ext_config = {}

    if IS_BUILDKITE:
        ext_config["registry"] = get_buildkite_registry_config()
    else:
        find_local_test_image(docker_image)

    @asset
    def number_x(
        context: AssetExecutionContext,
        pipes_client: PipesDockerClient,
    ):
        return pipes_client.run(
            image=docker_image,
            command=[
                "python",
                "-m",
                "numbers_example.number_x",
            ],
            context=context,
            extras={"storage_root": "/tmp/", "multiplier": 2},
            env={"PYTHONPATH": "/dagster_test/toys/external_execution/"},
        ).get_results()

    result = materialize(
        [number_x],
        resources={"pipes_client": PipesDockerClient(**ext_config)},
        raise_on_error=False,
    )
    assert result.success
    mats = result.asset_materializations_for_node(number_x.op.name)
    assert mats[0].metadata["path"]


@pytest.mark.integration
def test_file_io():
    docker_image = get_test_project_docker_image()

    registry = None

    if IS_BUILDKITE:
        registry = get_buildkite_registry_config()
    else:
        find_local_test_image(docker_image)

    with tempfile.TemporaryDirectory() as tempdir:

        @asset
        def number_x(
            context: AssetExecutionContext,
            pipes_client: PipesDockerClient,
        ):
            instance_storage = context.instance.storage_directory()
            host_storage = os.path.join(instance_storage, "number_example")
            os.makedirs(host_storage, exist_ok=True)

            container_storage = "/mnt/asset_storage/"

            volumes = {
                host_storage: {
                    "bind": container_storage,
                    "mode": "rw",
                },
                tempdir: {
                    "bind": tempdir,
                    "mode": "rw",
                },
            }

            return pipes_client.run(
                image=docker_image,
                command=[
                    "python",
                    "-m",
                    "numbers_example.number_x",
                ],
                registry=registry,
                context=context,
                extras={"storage_root": container_storage, "multiplier": 2},
                container_kwargs={
                    "environment": {"PYTHONPATH": "/dagster_test/toys/external_execution/"},
                    "volumes": volumes,
                },
            ).get_results()

        result = materialize(
            [number_x],
            resources={
                "pipes_client": PipesDockerClient(
                    context_injector=PipesFileContextInjector(os.path.join(tempdir, "context")),
                )
            },
            raise_on_error=False,
        )
        assert result.success
        mats = result.asset_materializations_for_node(number_x.op.name)
        assert mats[0].metadata["path"]


_print_script = """
import sys
import time

sys.stdout.write('w1')
print('p1')
sys.stdout.write('w2')
print('p2')
"""


@pytest.mark.integration
def test_bytes_logs():
    # docker_image = get_test_project_docker_image()

    # ext_config = {}

    # if IS_BUILDKITE:
    #     ext_config["registry"] = get_buildkite_registry_config()
    # else:
    #     find_local_test_image(docker_image)

    @asset
    def bytes_logs(
        context: AssetExecutionContext,
    ):
        c = PipesDockerClient()

        return c.run(
            context=context,
            image="python:3.10-slim",
            command=[
                "python",
                "-c",
                _print_script,
            ],
        ).get_results()

    result = materialize(
        [bytes_logs],
        raise_on_error=False,
    )
    assert result.success
