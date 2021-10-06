import subprocess

from dagster.grpc.types import ExecuteRunArgs
from dagster.core.test_utils import instance_for_test
from dagster.serdes.serdes import serialize_dagster_namedtuple
from dagster.utils.merger import merge_dicts
from . import docker_postgres_instance, IS_BUILDKITE
import os
import re
import time
from contextlib import contextmanager

import docker
import pytest
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import environ, poll_for_finished_run, poll_for_step_start
from dagster.utils.test.postgres_instance import postgres_instance_for_test
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


def test_image_on_pipeline():
    docker_image = get_test_project_docker_image()
    if IS_BUILDKITE:
        pass  # TODO
        # launcher_config["registry"] = get_buildkite_registry_config()
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
            },
        },
    )

    with docker_postgres_instance(
        overrides={
            "run_launcher": {
                "class": "DockerRunLauncher",
                "module": "dagster_docker",
                "config": {
                    "env_vars": [
                        "AWS_ACCESS_KEY_ID",
                        "AWS_SECRET_ACCESS_KEY",
                    ],
                    "network": "container:test-postgres-db-docker",
                    "container_kwargs": {"volumes": ["/var/run/docker.sock:/var/run/docker.sock"]},
                },
            }
        }
    ) as instance:
        recon_pipeline = get_test_project_recon_pipeline("demo_pipeline_docker", docker_image)
        with get_test_project_workspace_and_external_pipeline(
            instance, "demo_pipeline_docker", container_image=docker_image
        ) as (
            workspace,
            orig_pipeline,
        ):
            external_pipeline = ReOriginatedExternalPipelineForTest(
                orig_pipeline, container_image=docker_image
            )

            run = instance.create_run_for_pipeline(
                pipeline_def=recon_pipeline.get_definition(),
                run_config=run_config,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )

            instance.launch_run(run.run_id, workspace)

            poll_for_finished_run(instance, run.run_id, timeout=60)

            assert instance.get_run_by_id(run.run_id).status == PipelineRunStatus.SUCCESS


def test_recovery():
    docker_image = get_test_project_docker_image()
    if IS_BUILDKITE:
        pass  # TODO
        # launcher_config["registry"] = get_buildkite_registry_config()
    else:
        find_local_test_image(docker_image)

    run_config = merge_dicts(
        merge_yamls(
            [
                # os.path.join(get_test_project_environments_path(), "env.yaml"),
                os.path.join(get_test_project_environments_path(), "env_s3.yaml"),
            ]
        ),
        {
            "solids": {
                "multiply_the_word_slow": {
                    "inputs": {"word": "bar"},
                    "config": {"factor": 2, "sleep_time": 10},
                }
            },
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
            },
        },
    )

    with docker_postgres_instance(
        overrides={
            "run_launcher": {
                "class": "DockerRunLauncher",
                "module": "dagster_docker",
                "config": {
                    "env_vars": [
                        "AWS_ACCESS_KEY_ID",
                        "AWS_SECRET_ACCESS_KEY",
                    ],
                    "network": "container:test-postgres-db-docker",
                    "container_kwargs": {"volumes": ["/var/run/docker.sock:/var/run/docker.sock"]},
                },
            }
        }
    ) as instance:
        recon_pipeline = get_test_project_recon_pipeline("demo_pipeline_docker_slow", docker_image)
        with get_test_project_workspace_and_external_pipeline(
            instance, "demo_pipeline_docker_slow", container_image=docker_image
        ) as (
            workspace,
            orig_pipeline,
        ):
            external_pipeline = ReOriginatedExternalPipelineForTest(
                orig_pipeline, container_image=docker_image
            )

            run = instance.create_run_for_pipeline(
                pipeline_def=recon_pipeline.get_definition(),
                run_config=run_config,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )

            instance.launch_run(run.run_id, workspace)

            start_time = time.time()
            while time.time() - start_time < 60:
                run = instance.get_run_by_id(run.run_id)
                if run.status == PipelineRunStatus.STARTED:
                    break
                assert run.status == PipelineRunStatus.STARTING
                time.sleep(1)

            time.sleep(3)

            instance._run_launcher._get_container(instance.get_run_by_id(run.run_id)).stop(
                timeout=0
            )
            instance.launch_run(run.run_id, workspace, resume_from_failure=True)
            poll_for_finished_run(instance, run.run_id, timeout=60)

            for log in instance.all_logs(run.run_id):
                print(str(log) + "\n")
            assert instance.get_run_by_id(run.run_id).status == PipelineRunStatus.SUCCESS
