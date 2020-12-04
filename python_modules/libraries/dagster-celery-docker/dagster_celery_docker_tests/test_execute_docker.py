# pylint doesn't know about pytest fixtures
# pylint: disable=unused-argument

import os
from contextlib import contextmanager

from dagster import execute_pipeline
from dagster.utils import merge_dicts
from dagster.utils.test.postgres_instance import postgres_instance_for_test
from dagster.utils.yaml_utils import merge_yamls
from dagster_test.test_project import (
    find_local_test_image,
    get_buildkite_registry_config,
    get_test_project_docker_image,
    get_test_project_environments_path,
    get_test_project_recon_pipeline,
)

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@contextmanager
def celery_docker_postgres_instance(overrides=None):
    with postgres_instance_for_test(
        __file__, "test-postgres-db-celery-docker", overrides=overrides
    ) as instance:
        yield instance


def test_execute_celery_docker_image_on_executor_config():
    docker_image = get_test_project_docker_image()
    docker_config = {
        "image": docker_image,
        "env_vars": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",],
        "network": "container:test-postgres-db-celery-docker",
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


def test_execute_celery_docker_image_on_pipeline_config():
    docker_image = get_test_project_docker_image()
    docker_config = {
        "env_vars": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",],
        "network": "container:test-postgres-db-celery-docker",
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
