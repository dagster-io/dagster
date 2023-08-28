import os

import pytest
from dagster import AssetExecutionContext, asset, materialize
from dagster_docker.external_resource import DockerExecutionResource
from dagster_test.test_project import (
    IS_BUILDKITE,
    find_local_test_image,
    get_buildkite_registry_config,
    get_test_project_docker_image,
)


@pytest.mark.integration
def test_basic():
    docker_image = get_test_project_docker_image()

    launcher_config = {}

    if IS_BUILDKITE:
        launcher_config["registry"] = get_buildkite_registry_config()
    else:
        find_local_test_image(docker_image)

    @asset
    def number_x(
        context: AssetExecutionContext,
        docker_resource: DockerExecutionResource,
    ):
        instance_storage = context.instance.storage_directory()
        host_storage = os.path.join(instance_storage, "number_example")
        os.makedirs(host_storage, exist_ok=True)

        container_storage = "/mnt/asset_storage/"

        volumes = {
            host_storage: {
                "bind": container_storage,
                "mode": "rw",
            }
        }

        docker_resource.run(
            image=docker_image,
            command=[
                "python",
                "-m",
                "numbers_example.number_x",
            ],
            context=context,
            extras={"storage_root": container_storage, "multiplier": 2},
            env={"PYTHONPATH": "/dagster_test/toys/external_execution/"},
            volumes=volumes,
        )

    result = materialize(
        [number_x],
        resources={"docker_resource": DockerExecutionResource()},
        raise_on_error=False,
    )
    assert result.success
    mats = result.asset_materializations_for_node(number_x.op.name)
    assert mats[0].metadata["path"]
