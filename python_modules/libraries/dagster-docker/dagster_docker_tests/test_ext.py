import os
import tempfile

import pytest
from dagster import AssetExecutionContext, asset, materialize
from dagster._core.ext.utils import (
    ExtFileContextInjector,
)
from dagster_docker.ext import ExtDocker
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
        ext_docker: ExtDocker,
    ):
        ext_docker.run(
            image=docker_image,
            command=[
                "python",
                "-m",
                "numbers_example.number_x",
            ],
            context=context,
            extras={"storage_root": "/tmp/", "multiplier": 2},
            env={"PYTHONPATH": "/dagster_test/toys/external_execution/"},
        )

    result = materialize(
        [number_x],
        resources={"ext_docker": ExtDocker(**ext_config)},
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
            ext_docker: ExtDocker,
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

            ext_docker.run(
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
            )

        result = materialize(
            [number_x],
            resources={
                "ext_docker": ExtDocker(
                    context_injector=ExtFileContextInjector(os.path.join(tempdir, "context"))
                )
            },
            raise_on_error=False,
        )
        assert result.success
        mats = result.asset_materializations_for_node(number_x.op.name)
        assert mats[0].metadata["path"]
