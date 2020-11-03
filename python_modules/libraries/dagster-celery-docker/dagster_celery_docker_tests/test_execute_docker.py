# pylint doesn't know about pytest fixtures
# pylint: disable=unused-argument

import base64
import os
import sys
from contextlib import contextmanager

import boto3
import docker
import pytest
from dagster import execute_pipeline, file_relative_path, seven
from dagster.core.test_utils import instance_for_test_tempdir
from dagster.utils import merge_dicts
from dagster.utils.test.postgres_instance import TestPostgresInstance
from dagster.utils.yaml_utils import merge_yamls
from dagster_test.test_project import (
    build_and_tag_test_image,
    get_test_project_recon_pipeline,
    test_project_docker_image,
    test_project_environments_path,
)

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@contextmanager
def postgres_instance(overrides=None):
    with seven.TemporaryDirectory() as temp_dir:
        with TestPostgresInstance.docker_service_up_or_skip(
            file_relative_path(__file__, "docker-compose.yml"), "test-postgres-db-celery-docker",
        ) as pg_conn_string:
            TestPostgresInstance.clean_run_storage(pg_conn_string)
            TestPostgresInstance.clean_event_log_storage(pg_conn_string)
            TestPostgresInstance.clean_schedule_storage(pg_conn_string)
            with instance_for_test_tempdir(
                temp_dir,
                overrides=merge_dicts(
                    {
                        "run_storage": {
                            "module": "dagster_postgres.run_storage.run_storage",
                            "class": "PostgresRunStorage",
                            "config": {"postgres_url": pg_conn_string},
                        },
                        "event_log_storage": {
                            "module": "dagster_postgres.event_log.event_log",
                            "class": "PostgresEventLogStorage",
                            "config": {"postgres_url": pg_conn_string},
                        },
                        "schedule_storage": {
                            "module": "dagster_postgres.schedule_storage.schedule_storage",
                            "class": "PostgresScheduleStorage",
                            "config": {"postgres_url": pg_conn_string},
                        },
                    },
                    overrides if overrides else {},
                ),
            ) as instance:
                yield instance


@pytest.mark.integration
@pytest.mark.skipif(sys.version_info < (3, 5), reason="Very slow on Python 2")
def test_execute_celery_docker_image_on_executor_config():
    docker_image = test_project_docker_image()
    docker_config = {
        "image": docker_image,
        "env_vars": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",],
        "network": "container:test-postgres-db-celery-docker",
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

    with postgres_instance() as instance:

        result = execute_pipeline(
            get_test_project_recon_pipeline("docker_celery_pipeline"),
            run_config=run_config,
            instance=instance,
        )
        assert result.success


@pytest.mark.integration
@pytest.mark.skipif(sys.version_info < (3, 5), reason="Very slow on Python 2")
def test_execute_celery_docker_image_on_pipeline_config():
    docker_image = test_project_docker_image()
    docker_config = {
        "env_vars": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",],
        "network": "container:test-postgres-db-celery-docker",
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

    with postgres_instance() as instance:

        container_image = test_project_docker_image()

        result = execute_pipeline(
            get_test_project_recon_pipeline("docker_celery_pipeline", container_image),
            run_config=run_config,
            instance=instance,
        )
        assert result.success
