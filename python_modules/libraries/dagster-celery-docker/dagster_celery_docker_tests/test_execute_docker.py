# pylint doesn't know about pytest fixtures
# pylint: disable=unused-argument

import os
from contextlib import contextmanager

from dagster_test.test_project import (
    find_local_test_image,
    get_buildkite_registry_config,
    get_test_project_docker_image,
    get_test_project_environments_path,
    get_test_project_recon_pipeline,
)

from dagster._legacy import execute_pipeline
from dagster._utils import merge_dicts
from dagster._utils.test.postgres_instance import postgres_instance_for_test
from dagster._utils.yaml_utils import merge_yamls

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@contextmanager
def celery_docker_postgres_instance(overrides=None):
    with postgres_instance_for_test(
        __file__, "test-postgres-db-celery-docker", overrides=overrides
    ) as instance:
        yield instance


def test_execute_celery_docker_image_on_executor_config(aws_creds):
    docker_image = get_test_project_docker_image()
    docker_config = {
        "image": docker_image,
        "network": "container:test-postgres-db-celery-docker",
        "container_kwargs": {
            "environment": {
                "FIND_ME": "here!",
                "AWS_ACCESS_KEY_ID": aws_creds["aws_access_key_id"],
                "AWS_SECRET_ACCESS_KEY": aws_creds["aws_secret_access_key"],
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
                "celery-docker": {
                    "config": {
                        "docker": docker_config,
                        "config_source": {"task_always_eager": True},
                    }
                }
            },
        },
    )

    with celery_docker_postgres_instance() as instance:

        result = execute_pipeline(
            get_test_project_recon_pipeline("docker_celery_pipeline"),
            run_config=run_config,
            instance=instance,
        )
        assert result.success
        assert result.result_for_solid("get_environment_solid").output_value("result") == "here!"


def test_execute_celery_docker_image_on_pipeline_config(aws_creds):
    docker_image = get_test_project_docker_image()
    docker_config = {
        "network": "container:test-postgres-db-celery-docker",
        "container_kwargs": {
            "environment": [
                "FIND_ME=here!",
                f"AWS_ACCESS_KEY_ID={aws_creds['aws_access_key_id']}",
                f"AWS_SECRET_ACCESS_KEY={aws_creds['aws_secret_access_key']}",
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
                "celery-docker": {
                    "config": {
                        "docker": docker_config,
                        "config_source": {"task_always_eager": True},
                    }
                }
            },
        },
    )

    with celery_docker_postgres_instance() as instance:
        result = execute_pipeline(
            get_test_project_recon_pipeline("docker_celery_pipeline", docker_image),
            run_config=run_config,
            instance=instance,
        )
        assert result.success
        assert result.result_for_solid("get_environment_solid").output_value("result") == "here!"
