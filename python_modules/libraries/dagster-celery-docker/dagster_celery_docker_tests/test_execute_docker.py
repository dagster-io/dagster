# pylint doesn't know about pytest fixtures


import os
from contextlib import contextmanager

import pytest
from dagster._core.execution.api import execute_job
from dagster._core.test_utils import environ
from dagster._utils.merger import merge_dicts
from dagster_shared.yaml_utils import merge_yamls
from dagster_test.test_project import (
    find_local_test_image,
    get_buildkite_registry_config,
    get_test_project_docker_image,
    get_test_project_environments_path,
    get_test_project_recon_job,
)

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@pytest.fixture
def celery_docker_postgres_instance(postgres_instance):
    @contextmanager
    def _instance(overrides=None):
        with postgres_instance(overrides=overrides) as instance:
            yield instance

    return _instance


@pytest.mark.integration
def test_execute_celery_docker_image_on_executor_config(
    celery_docker_postgres_instance, aws_env_from_pytest, aws_env_from_dagster_container, bucket
):
    docker_image = get_test_project_docker_image()
    docker_config = {
        "image": docker_image,
        "network": "container:postgres",
        "container_kwargs": {
            "environment": {
                "FIND_ME": "here!",
                **aws_env_from_dagster_container,
            },
            # "auto_remove": False # uncomment when debugging to view container logs after execution
        },
    }

    if IS_BUILDKITE:
        docker_config["registry"] = get_buildkite_registry_config()
    else:
        find_local_test_image(docker_image)

    run_config = merge_dicts(
        merge_yamls(
            [
                os.path.join(get_test_project_environments_path(), "env.yaml"),
                os.path.join(get_test_project_environments_path(), "env_s3.yaml"),
                os.path.join(get_test_project_environments_path(), "env_environment_vars.yaml"),
            ]
        ),
        {
            "execution": {
                "config": {
                    "docker": docker_config,
                    "config_source": {"task_always_eager": True},
                }
            },
        },
    )

    with celery_docker_postgres_instance() as instance, environ(aws_env_from_pytest):
        with execute_job(
            get_test_project_recon_job("docker_celery_job"),
            run_config=run_config,
            instance=instance,
        ) as result:
            assert result.success
            assert result.output_for_node("get_environment") == "here!"


@pytest.mark.integration
def test_execute_celery_docker_image_on_job_config(
    celery_docker_postgres_instance, aws_env_from_pytest, aws_env_from_dagster_container, bucket
):
    docker_image = get_test_project_docker_image()
    docker_config = {
        "network": "container:postgres",
        "container_kwargs": {
            "environment": [
                "FIND_ME=here!",
                *[f"{k}={v}" for k, v in aws_env_from_dagster_container.items()],
            ],
            # "auto_remove": False # uncomment when debugging to view container logs after execution
        },
    }

    if IS_BUILDKITE:
        docker_config["registry"] = get_buildkite_registry_config()

    else:
        find_local_test_image(docker_image)

    run_config = merge_dicts(
        merge_yamls(
            [
                os.path.join(get_test_project_environments_path(), "env.yaml"),
                os.path.join(get_test_project_environments_path(), "env_s3.yaml"),
                os.path.join(get_test_project_environments_path(), "env_environment_vars.yaml"),
            ]
        ),
        {
            "execution": {
                "config": {
                    "docker": docker_config,
                    "config_source": {"task_always_eager": True},
                }
            },
        },
    )

    with celery_docker_postgres_instance() as instance, environ(aws_env_from_pytest):
        with execute_job(
            get_test_project_recon_job("docker_celery_job", docker_image),
            run_config=run_config,
            instance=instance,
        ) as result:
            assert result.success
            assert result.output_for_node("get_environment") == "here!"
