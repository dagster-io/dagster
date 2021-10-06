# pylint doesn't know about pytest fixtures
# pylint: disable=unused-argument

import os
import re
import time
from dagster.core.execution.api import execute_pipeline
from dagster.utils.merger import merge_dicts
from dagster_test.test_project import (
    ReOriginatedExternalPipelineForTest,
    find_local_test_image,
    get_buildkite_registry_config,
    get_test_project_docker_image,
    get_test_project_environments_path,
    get_test_project_recon_pipeline,
    get_test_project_workspace_and_external_pipeline,
)
import docker
import pytest
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import environ, poll_for_finished_run, poll_for_step_start
from dagster.utils.yaml_utils import merge_yamls
from dagster_docker.docker_run_launcher import DOCKER_CONTAINER_ID_TAG, DOCKER_IMAGE_TAG
from dagster_test.test_project import (
    ReOriginatedExternalPipelineForTest,
    find_local_test_image,
    get_buildkite_registry_config,
    get_test_project_docker_image,
    get_test_project_environments_path,
    get_test_project_recon_pipeline,
    get_test_project_workspace_and_external_pipeline,
)

from . import docker_postgres_instance, IS_BUILDKITE


def test_docker_executor():
    """
    Note that this test relies on having AWS credentials in the environment.
    """
    docker_image = get_test_project_docker_image()
    if IS_BUILDKITE:
        # TODO!
        pass
    else:
        find_local_test_image(docker_image)

    run_config = merge_dicts(
        merge_yamls(
            [
                os.path.join(get_test_project_environments_path(), "env.yaml"),
                os.path.join(get_test_project_environments_path(), "env_s3.yaml"),
            ]
        ),
        {
            "execution": {
                "docker": {
                    "config": {
                        "networks": ["container:test-postgres-db-docker"],
                        "env_vars": [
                            "AWS_ACCESS_KEY_ID",
                            "AWS_SECRET_ACCESS_KEY",
                        ],
                    }
                }
            }
        },
    )

    with environ({"DOCKER_LAUNCHER_NETWORK": "container:test-postgres-db-docker"}):
        with docker_postgres_instance() as instance:
            recon_pipeline = get_test_project_recon_pipeline("demo_pipeline_docker", docker_image)
            assert execute_pipeline(
                recon_pipeline, run_config=run_config, instance=instance
            ).success


def test_docker_executor_check_step_health():
    # missing network causes step to fail
    docker_image = get_test_project_docker_image()
    if IS_BUILDKITE:
        # TODO!
        pass
    else:
        find_local_test_image(docker_image)

    run_config = merge_dicts(
        merge_yamls(
            [
                os.path.join(get_test_project_environments_path(), "env.yaml"),
                os.path.join(get_test_project_environments_path(), "env_s3.yaml"),
            ]
        ),
        {
            "execution": {
                "docker": {
                    "config": {
                        "env_vars": [
                            "AWS_ACCESS_KEY_ID",
                            "AWS_SECRET_ACCESS_KEY",
                        ],
                    }
                }
            }
        },
    )

    with environ({"DOCKER_LAUNCHER_NETWORK": "container:test-postgres-db-docker"}):
        with docker_postgres_instance() as instance:
            recon_pipeline = get_test_project_recon_pipeline("demo_pipeline_docker", docker_image)
            assert not execute_pipeline(
                recon_pipeline, run_config=run_config, instance=instance
            ).success
