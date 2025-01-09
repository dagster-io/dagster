import datetime
import os
import time
from collections.abc import Mapping
from typing import Any

import boto3
from dagster import DagsterEventType
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.storage.tags import DOCKER_IMAGE_TAG
from dagster._utils.merger import merge_dicts
from dagster._utils.yaml_utils import merge_yamls
from dagster_k8s.test import wait_for_job_and_get_raw_logs
from dagster_k8s_test_infra.integration_utils import (
    can_terminate_run_over_graphql,
    image_pull_policy,
    launch_run_over_graphql,
    terminate_run_over_graphql,
)
from dagster_test.test_project import get_test_project_environments_path

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


def get_celery_engine_config(
    dagster_docker_image: str, job_namespace: str, include_dagster_job_env: bool = False
) -> Mapping[str, Any]:
    return {
        "execution": {
            "config": merge_dicts(
                (
                    {
                        "job_image": dagster_docker_image,
                    }
                    if dagster_docker_image
                    else {}
                ),
                {
                    "job_namespace": job_namespace,
                    "image_pull_policy": image_pull_policy(),
                },
                ({"env_config_maps": ["dagster-pipeline-env"]} if include_dagster_job_env else {}),
            )
        },
    }


def test_execute_on_celery_k8s_default(
    dagster_docker_image,
    dagster_instance,
    helm_namespace,
    webserver_url,
):
    run_config = merge_dicts(
        merge_yamls(
            [
                os.path.join(get_test_project_environments_path(), "env.yaml"),
                os.path.join(get_test_project_environments_path(), "env_s3.yaml"),
            ]
        ),
        get_celery_engine_config(
            dagster_docker_image=dagster_docker_image, job_namespace=helm_namespace
        ),
    )

    run_id = launch_run_over_graphql(
        webserver_url, run_config=run_config, job_name="demo_job_celery_k8s"
    )

    result = wait_for_job_and_get_raw_logs(
        job_name=f"dagster-run-{run_id}",
        namespace=helm_namespace,
    )

    assert "RUN_SUCCESS" in result, f"no match, result: {result}"

    updated_run = dagster_instance.get_run_by_id(run_id)
    assert updated_run.tags[DOCKER_IMAGE_TAG] == dagster_docker_image


def _test_termination(webserver_url, dagster_instance, run_config):
    run_id = launch_run_over_graphql(
        webserver_url, run_config=run_config, job_name="resource_job_celery_k8s"
    )

    # Wait for run to start
    timeout = datetime.timedelta(0, 120)
    start_time = datetime.datetime.now()

    while True:
        assert datetime.datetime.now() < start_time + timeout, "Timed out waiting for can_terminate"
        dagster_run = dagster_instance.get_run_by_id(run_id)
        if can_terminate_run_over_graphql(webserver_url, run_id):
            break
        time.sleep(5)

    # Wait for step to start
    step_start_found = False
    start_time = datetime.datetime.now()
    while datetime.datetime.now() < start_time + timeout:
        event_records = dagster_instance.all_logs(run_id)
        for event_record in event_records:
            if (
                event_record.dagster_event
                and event_record.dagster_event.event_type == DagsterEventType.STEP_START
            ):
                step_start_found = True
                break

        if step_start_found:
            break

        time.sleep(5)
    assert step_start_found

    # Terminate run
    assert can_terminate_run_over_graphql(webserver_url, run_id=run_id)
    terminate_run_over_graphql(webserver_url, run_id=run_id)

    # Check that run is marked as canceled
    dagster_run_status_canceled = False
    start_time = datetime.datetime.now()
    while datetime.datetime.now() < start_time + timeout:
        dagster_run = dagster_instance.get_run_by_id(run_id)
        if dagster_run.status == DagsterRunStatus.CANCELED:
            dagster_run_status_canceled = True
            break
        time.sleep(5)
    assert dagster_run_status_canceled

    # Check that terminate cannot be called again
    assert not can_terminate_run_over_graphql(webserver_url, run_id=run_id)

    # Check for step failure and resource tear down
    expected_events_found = False
    start_time = datetime.datetime.now()
    while datetime.datetime.now() < start_time + timeout:
        step_failures_count = 0
        resource_tear_down_count = 0
        resource_init_count = 0
        termination_request_count = 0
        termination_success_count = 0
        event_records = dagster_instance.all_logs(run_id)
        for event_record in event_records:
            if event_record.dagster_event:
                if event_record.dagster_event.event_type == DagsterEventType.STEP_FAILURE:
                    step_failures_count += 1
                elif event_record.dagster_event.event_type == DagsterEventType.PIPELINE_CANCELING:
                    termination_request_count += 1
                elif event_record.dagster_event.event_type == DagsterEventType.PIPELINE_CANCELED:
                    termination_success_count += 1
            elif event_record.message:
                if "initializing s3_resource_with_context_manager" in event_record.message:
                    resource_init_count += 1
                if "tearing down s3_resource_with_context_manager" in event_record.message:
                    resource_tear_down_count += 1
        if (
            step_failures_count == 1
            and resource_init_count == 1
            and resource_tear_down_count == 1
            and termination_request_count == 1
            and termination_success_count == 1
        ):
            expected_events_found = True
            break
        time.sleep(5)
    assert expected_events_found

    s3 = boto3.resource("s3", region_name="us-west-1", use_ssl=True, endpoint_url=None).meta.client
    bucket = "dagster-scratch-80542c2"
    key = f"resource_termination_test/{run_id}"
    assert s3.get_object(Bucket=bucket, Key=key)


def test_execute_on_celery_k8s_with_termination(
    dagster_docker_image,
    dagster_instance,
    helm_namespace,
    webserver_url,
):
    run_config = merge_dicts(
        merge_yamls(
            [
                os.path.join(get_test_project_environments_path(), "env_s3.yaml"),
            ]
        ),
        get_celery_engine_config(
            dagster_docker_image=dagster_docker_image, job_namespace=helm_namespace
        ),
    )

    _test_termination(webserver_url, dagster_instance, run_config)
