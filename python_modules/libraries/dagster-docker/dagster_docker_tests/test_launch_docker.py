# pylint doesn't know about pytest fixtures
# pylint: disable=unused-argument

import os
from contextlib import contextmanager

from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import poll_for_finished_run, poll_for_step_start
from dagster.utils.test.postgres_instance import postgres_instance_for_test
from dagster.utils.yaml_utils import merge_yamls
from dagster_test.test_project import (
    ReOriginatedExternalPipelineForTest,
    find_local_test_image,
    get_buildkite_registry_config,
    get_test_project_docker_image,
    get_test_project_environments_path,
    get_test_project_external_pipeline,
    get_test_project_recon_pipeline,
)

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@contextmanager
def docker_postgres_instance(overrides=None):
    with postgres_instance_for_test(
        __file__, "test-postgres-db-docker", overrides=overrides
    ) as instance:
        yield instance


def test_launch_docker_image_on_pipeline_config():
    # Docker image name to use for launch specified as part of the pipeline origin
    # rather than in the run launcher instance config

    docker_image = get_test_project_docker_image()
    launcher_config = {
        "env_vars": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",],
        "network": "container:test-postgres-db-docker",
    }

    if IS_BUILDKITE:
        launcher_config["registry"] = get_buildkite_registry_config()
    else:
        find_local_test_image(docker_image)

    run_config = merge_yamls(
        [
            os.path.join(get_test_project_environments_path(), "env.yaml"),
            os.path.join(get_test_project_environments_path(), "env_s3.yaml"),
        ]
    )

    with docker_postgres_instance(
        overrides={
            "run_launcher": {
                "class": "DockerRunLauncher",
                "module": "dagster_docker",
                "config": launcher_config,
            }
        }
    ) as instance:
        recon_pipeline = get_test_project_recon_pipeline("demo_pipeline", docker_image)
        run = instance.create_run_for_pipeline(
            pipeline_def=recon_pipeline.get_definition(), run_config=run_config,
        )

        external_pipeline = ReOriginatedExternalPipelineForTest(
            get_test_project_external_pipeline("demo_pipeline", container_image=docker_image),
            container_image=docker_image,
        )
        instance.launch_run(run.run_id, external_pipeline)

        poll_for_finished_run(instance, run.run_id, timeout=60)

        assert instance.get_run_by_id(run.run_id).status == PipelineRunStatus.SUCCESS


def _check_event_log_contains(event_log, expected_type_and_message):
    types_and_messages = [
        (e.dagster_event.event_type_value, e.message) for e in event_log if e.is_dagster_event
    ]

    for expected_event_type, expected_message_fragment in expected_type_and_message:
        assert any(
            event_type == expected_event_type and expected_message_fragment in message
            for event_type, message in types_and_messages
        )


def test_terminate_launched_docker_run():
    docker_image = get_test_project_docker_image()
    launcher_config = {
        "env_vars": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",],
        "network": "container:test-postgres-db-docker",
    }

    if IS_BUILDKITE:
        launcher_config["registry"] = get_buildkite_registry_config()
    else:
        find_local_test_image(docker_image)

    run_config = merge_yamls([os.path.join(get_test_project_environments_path(), "env_s3.yaml"),])

    with docker_postgres_instance(
        overrides={
            "run_launcher": {
                "class": "DockerRunLauncher",
                "module": "dagster_docker",
                "config": launcher_config,
            }
        }
    ) as instance:
        recon_pipeline = get_test_project_recon_pipeline("hanging_pipeline", docker_image)
        run = instance.create_run_for_pipeline(
            pipeline_def=recon_pipeline.get_definition(), run_config=run_config,
        )

        run_id = run.run_id

        external_pipeline = ReOriginatedExternalPipelineForTest(
            get_test_project_external_pipeline("hanging_pipeline", container_image=docker_image),
            container_image=docker_image,
        )
        instance.launch_run(run_id, external_pipeline)

        poll_for_step_start(instance, run_id)

        assert instance.run_launcher.can_terminate(run_id)
        assert instance.run_launcher.terminate(run_id)

        terminated_pipeline_run = poll_for_finished_run(instance, run_id, timeout=30)
        terminated_pipeline_run = instance.get_run_by_id(run_id)
        assert terminated_pipeline_run.status == PipelineRunStatus.CANCELED

        run_logs = instance.all_logs(run_id)

        _check_event_log_contains(
            run_logs,
            [
                ("PIPELINE_CANCELING", "Sending pipeline termination request"),
                ("STEP_FAILURE", 'Execution of step "hanging_solid" failed.'),
                ("PIPELINE_CANCELED", 'Execution of pipeline "hanging_pipeline" canceled.'),
                ("ENGINE_EVENT", "Pipeline execution terminated by interrupt"),
                ("ENGINE_EVENT", "Process for pipeline exited"),
            ],
        )


def test_launch_docker_image_on_instance_config():
    docker_image = get_test_project_docker_image()
    launcher_config = {
        "env_vars": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",],
        "network": "container:test-postgres-db-docker",
        "image": docker_image,
    }

    if IS_BUILDKITE:
        launcher_config["registry"] = get_buildkite_registry_config()
    else:
        find_local_test_image(docker_image)

    run_config = merge_yamls(
        [
            os.path.join(get_test_project_environments_path(), "env.yaml"),
            os.path.join(get_test_project_environments_path(), "env_s3.yaml"),
        ]
    )

    with docker_postgres_instance(
        overrides={
            "run_launcher": {
                "class": "DockerRunLauncher",
                "module": "dagster_docker",
                "config": launcher_config,
            }
        }
    ) as instance:
        recon_pipeline = get_test_project_recon_pipeline("demo_pipeline")
        run = instance.create_run_for_pipeline(
            pipeline_def=recon_pipeline.get_definition(), run_config=run_config,
        )

        external_pipeline = ReOriginatedExternalPipelineForTest(
            get_test_project_external_pipeline("demo_pipeline")
        )
        instance.launch_run(run.run_id, external_pipeline)

        poll_for_finished_run(instance, run.run_id, timeout=60)

        assert instance.get_run_by_id(run.run_id).status == PipelineRunStatus.SUCCESS
