import os
import sys

import pytest
from dagster.core.test_utils import create_run_for_test
from dagster.utils import merge_dicts
from dagster.utils.yaml_utils import merge_yamls
from dagster_k8s.test import wait_for_job_and_get_raw_logs
from dagster_test.test_project import (
    ReOriginatedExternalPipelineForTest,
    get_test_project_external_pipeline,
    test_project_environments_path,
)
from marks import mark_run_coordinator


def get_celery_engine_config(dagster_docker_image, job_namespace):
    return {
        "execution": {
            "celery-k8s": {
                "config": {
                    "job_image": dagster_docker_image,
                    "job_namespace": job_namespace,
                    "image_pull_policy": "Always",
                    "env_config_maps": ["dagster-pipeline-env"],
                }
            }
        },
    }


def assert_events_in_order(logs, expected_events):

    logged_events = [log.dagster_event.event_type_value for log in logs]
    filtered_logged_events = [event for event in logged_events if event in expected_events]

    assert filtered_logged_events == expected_events


@mark_run_coordinator
@pytest.mark.integration
@pytest.mark.skipif(sys.version_info < (3, 5), reason="Very slow on Python 2")
def test_execute_on_celery_k8s(  # pylint: disable=redefined-outer-name
    dagster_docker_image, dagster_instance_for_run_coordinator, helm_namespace_for_run_coordinator
):
    run_config = merge_dicts(
        merge_yamls(
            [
                os.path.join(test_project_environments_path(), "env.yaml"),
                os.path.join(test_project_environments_path(), "env_s3.yaml"),
            ]
        ),
        get_celery_engine_config(
            dagster_docker_image=dagster_docker_image,
            job_namespace=helm_namespace_for_run_coordinator,
        ),
    )
    pipeline_name = "demo_pipeline_celery"
    external_pipeline = get_test_project_external_pipeline(pipeline_name)
    reoriginated_pipeline = ReOriginatedExternalPipelineForTest(external_pipeline)
    run = create_run_for_test(
        dagster_instance_for_run_coordinator,
        pipeline_name=pipeline_name,
        run_config=run_config,
        mode="default",
        external_pipeline_origin=reoriginated_pipeline.get_external_origin(),
    )

    dagster_instance_for_run_coordinator.submit_run(
        run.run_id, reoriginated_pipeline,
    )

    wait_for_job_and_get_raw_logs(
        job_name="dagster-run-%s" % run.run_id, namespace=helm_namespace_for_run_coordinator
    )

    logs = dagster_instance_for_run_coordinator.all_logs(run.run_id)
    assert_events_in_order(
        logs, ["PIPELINE_ENQUEUED", "PIPELINE_DEQUEUED", "PIPELINE_SUCCESS"],
    )
