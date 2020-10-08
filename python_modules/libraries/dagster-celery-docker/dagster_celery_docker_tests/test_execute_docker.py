# pylint doesn't know about pytest fixtures
# pylint: disable=unused-argument

import base64
import os
import sys

import boto3
import docker
import pytest
from dagster_test.test_project import (
    build_and_tag_test_image,
    get_test_project_recon_pipeline,
    test_project_docker_image,
    test_project_environments_path,
)

from dagster import DagsterInstance, execute_pipeline, seven
from dagster.utils import merge_dicts
from dagster.utils.yaml_utils import merge_yamls

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@pytest.mark.integration
@pytest.mark.skipif(sys.version_info < (3, 5), reason="Very slow on Python 2")
def test_execute_celery_docker():
    docker_image = test_project_docker_image()
    docker_config = {
        "image": docker_image,
        "env_vars": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    }

    if IS_BUILDKITE:
        ecr_client = boto3.client("ecr", region_name="us-west-1")
        token = ecr_client.get_authorization_token()
        username, password = (
            base64.b64decode(token["authorizationData"][0]["authorizationToken"])
            .decode()
            .split(":")
        )
        registry = token["authorizationData"][0]["proxyEndpoint"]

        docker_config["registry"] = {
            "url": registry,
            "username": username,
            "password": password,
        }

    else:
        try:
            client = docker.from_env()
            client.images.get(docker_image)
            print(  # pylint: disable=print-call
                "Found existing image tagged {image}, skipping image build. To rebuild, first run: "
                "docker rmi {image}".format(image=docker_image)
            )
        except docker.errors.ImageNotFound:
            build_and_tag_test_image(docker_image)

    with seven.TemporaryDirectory() as temp_dir:

        run_config = merge_dicts(
            merge_yamls(
                [
                    os.path.join(test_project_environments_path(), "env.yaml"),
                    os.path.join(test_project_environments_path(), "env_s3.yaml"),
                ]
            ),
            {
                "execution": {
                    "celery-docker": {
                        "config": {
                            "docker": docker_config,
                            "config_source": {"task_always_eager": True},
                        }
                    }
                },
            },
        )

        result = execute_pipeline(
            get_test_project_recon_pipeline("docker_celery_pipeline"),
            run_config=run_config,
            instance=DagsterInstance.local_temp(temp_dir),
        )
        assert result.success
