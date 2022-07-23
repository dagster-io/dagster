import os

from dagster_k8s.test import wait_for_job_and_get_raw_logs
from dagster_k8s_test_infra.integration_utils import image_pull_policy, launch_run_over_graphql
from dagster_test.test_project import get_test_project_environments_path
from marks import mark_daemon

from dagster._utils import merge_dicts
from dagster._utils.yaml_utils import merge_yamls


def get_celery_engine_config(dagster_docker_image, job_namespace):
    return {
        "execution": {
            "celery-k8s": {
                "config": {
                    "job_image": dagster_docker_image,
                    "job_namespace": job_namespace,
                    "image_pull_policy": image_pull_policy(),
                }
            }
        },
    }


def assert_events_in_order(logs, expected_events):

    logged_events = [log.dagster_event.event_type_value for log in logs if log.is_dagster_event]
    filtered_logged_events = [event for event in logged_events if event in expected_events]

    assert filtered_logged_events == expected_events


@mark_daemon
def test_execute_queued_run_on_celery_k8s(  # pylint: disable=redefined-outer-name
    dagster_docker_image,
    dagster_instance_for_daemon,
    helm_namespace_for_daemon,
    dagit_url_for_daemon,
):
    run_config = merge_dicts(
        merge_yamls(
            [
                os.path.join(get_test_project_environments_path(), "env.yaml"),
                os.path.join(get_test_project_environments_path(), "env_s3.yaml"),
            ]
        ),
        get_celery_engine_config(
            dagster_docker_image=dagster_docker_image,
            job_namespace=helm_namespace_for_daemon,
        ),
    )

    run_id = launch_run_over_graphql(
        dagit_url_for_daemon, run_config=run_config, pipeline_name="demo_pipeline_celery"
    )

    wait_for_job_and_get_raw_logs(
        job_name="dagster-run-%s" % run_id, namespace=helm_namespace_for_daemon
    )

    logs = dagster_instance_for_daemon.all_logs(run_id)
    assert_events_in_order(
        logs,
        ["PIPELINE_ENQUEUED", "PIPELINE_DEQUEUED", "PIPELINE_STARTING", "PIPELINE_SUCCESS"],
    )
