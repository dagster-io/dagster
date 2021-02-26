# pylint doesn't know about pytest fixtures
# pylint: disable=unused-argument
import datetime
import os
import time

import boto3
import pytest
from dagster import DagsterEventType
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import create_run_for_test
from dagster.utils import merge_dicts
from dagster.utils.yaml_utils import merge_yamls
from dagster_celery_k8s.launcher import CeleryK8sRunLauncher
from dagster_k8s.test import wait_for_job_and_get_raw_logs
from dagster_k8s_test_infra.helm import TEST_AWS_CONFIGMAP_NAME
from dagster_k8s_test_infra.integration_utils import image_pull_policy
from dagster_test.test_project import (
    ReOriginatedExternalPipelineForTest,
    get_test_project_environments_path,
    get_test_project_external_pipeline,
)

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


def get_celery_engine_config(dagster_docker_image, job_namespace):
    return {
        "execution": {
            "celery-k8s": {
                "config": {
                    "job_image": dagster_docker_image,
                    "job_namespace": job_namespace,
                    "image_pull_policy": image_pull_policy(),
                    "env_config_maps": ["dagster-pipeline-env"]
                    + ([TEST_AWS_CONFIGMAP_NAME] if not IS_BUILDKITE else []),
                }
            }
        },
    }


def test_execute_on_celery_k8s_default(  # pylint: disable=redefined-outer-name
    dagster_docker_image, dagster_instance, helm_namespace
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

    pipeline_name = "demo_pipeline_celery"
    run = create_run_for_test(
        dagster_instance,
        pipeline_name=pipeline_name,
        run_config=run_config,
        mode="default",
    )

    dagster_instance.launch_run(
        run.run_id,
        ReOriginatedExternalPipelineForTest(get_test_project_external_pipeline(pipeline_name)),
    )

    result = wait_for_job_and_get_raw_logs(
        job_name="dagster-run-%s" % run.run_id, namespace=helm_namespace
    )

    assert "PIPELINE_SUCCESS" in result, "no match, result: {}".format(result)


def test_execute_subset_on_celery_k8s(  # pylint: disable=redefined-outer-name
    dagster_docker_image, dagster_instance, helm_namespace
):
    run_config = merge_dicts(
        merge_yamls(
            [
                os.path.join(get_test_project_environments_path(), "env_subset.yaml"),
                os.path.join(get_test_project_environments_path(), "env_s3.yaml"),
            ]
        ),
        get_celery_engine_config(
            dagster_docker_image=dagster_docker_image, job_namespace=helm_namespace
        ),
    )

    pipeline_name = "demo_pipeline_celery"
    run = create_run_for_test(
        dagster_instance,
        pipeline_name=pipeline_name,
        run_config=run_config,
        mode="default",
        solids_to_execute={"count_letters"},
    )

    dagster_instance.launch_run(
        run.run_id,
        ReOriginatedExternalPipelineForTest(get_test_project_external_pipeline(pipeline_name)),
    )

    result = wait_for_job_and_get_raw_logs(
        job_name="dagster-run-%s" % run.run_id, namespace=helm_namespace
    )

    assert "PIPELINE_SUCCESS" in result, "no match, result: {}".format(result)


def test_execute_on_celery_k8s_retry_pipeline(  # pylint: disable=redefined-outer-name
    dagster_docker_image, dagster_instance, helm_namespace
):
    run_config = merge_dicts(
        merge_yamls([os.path.join(get_test_project_environments_path(), "env_s3.yaml")]),
        get_celery_engine_config(
            dagster_docker_image=dagster_docker_image, job_namespace=helm_namespace
        ),
    )

    pipeline_name = "retry_pipeline"
    run = create_run_for_test(
        dagster_instance,
        pipeline_name=pipeline_name,
        run_config=run_config,
        mode="default",
    )

    dagster_instance.launch_run(
        run.run_id,
        ReOriginatedExternalPipelineForTest(get_test_project_external_pipeline(pipeline_name)),
    )

    result = wait_for_job_and_get_raw_logs(
        job_name="dagster-run-%s" % run.run_id, namespace=helm_namespace
    )

    assert "PIPELINE_SUCCESS" in result, "no match, result: {}".format(result)

    stats = dagster_instance.get_run_stats(run.run_id)
    assert stats.steps_succeeded == 1

    assert DagsterEventType.STEP_START in [
        event.dagster_event.event_type
        for event in dagster_instance.all_logs(run.run_id)
        if event.is_dagster_event
    ]

    assert DagsterEventType.STEP_UP_FOR_RETRY in [
        event.dagster_event.event_type
        for event in dagster_instance.all_logs(run.run_id)
        if event.is_dagster_event
    ]

    assert DagsterEventType.STEP_RESTARTED in [
        event.dagster_event.event_type
        for event in dagster_instance.all_logs(run.run_id)
        if event.is_dagster_event
    ]

    assert DagsterEventType.STEP_SUCCESS in [
        event.dagster_event.event_type
        for event in dagster_instance.all_logs(run.run_id)
        if event.is_dagster_event
    ]


def test_execute_on_celery_k8s_with_resource_requirements(  # pylint: disable=redefined-outer-name
    dagster_docker_image, dagster_instance, helm_namespace
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

    pipeline_name = "resources_limit_pipeline_celery"
    run = create_run_for_test(
        dagster_instance,
        pipeline_name=pipeline_name,
        run_config=run_config,
        mode="default",
    )

    dagster_instance.launch_run(
        run.run_id,
        ReOriginatedExternalPipelineForTest(get_test_project_external_pipeline(pipeline_name)),
    )

    result = wait_for_job_and_get_raw_logs(
        job_name="dagster-run-%s" % run.run_id, namespace=helm_namespace
    )

    assert "PIPELINE_SUCCESS" in result, "no match, result: {}".format(result)


def _test_termination(dagster_instance, run_config):
    pipeline_name = "resource_pipeline"
    run = create_run_for_test(
        dagster_instance,
        pipeline_name=pipeline_name,
        run_config=run_config,
        mode="default",
    )

    dagster_instance.launch_run(
        run.run_id,
        ReOriginatedExternalPipelineForTest(get_test_project_external_pipeline(pipeline_name)),
    )
    assert isinstance(dagster_instance.run_launcher, CeleryK8sRunLauncher)

    # Wait for pipeline run to start
    timeout = datetime.timedelta(0, 120)
    start_time = datetime.datetime.now()
    can_terminate = False
    while datetime.datetime.now() < start_time + timeout:
        if dagster_instance.run_launcher.can_terminate(run_id=run.run_id):
            can_terminate = True
            break
        time.sleep(5)
    assert can_terminate

    # Wait for step to start
    step_start_found = False
    start_time = datetime.datetime.now()
    while datetime.datetime.now() < start_time + timeout:
        event_records = dagster_instance.all_logs(run.run_id)
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
    assert dagster_instance.run_launcher.can_terminate(run_id=run.run_id)
    assert dagster_instance.run_launcher.terminate(run_id=run.run_id)

    # Check that pipeline run is marked as canceled
    pipeline_run_status_canceled = False
    start_time = datetime.datetime.now()
    while datetime.datetime.now() < start_time + timeout:
        pipeline_run = dagster_instance.get_run_by_id(run.run_id)
        if pipeline_run.status == PipelineRunStatus.CANCELED:
            pipeline_run_status_canceled = True
            break
        time.sleep(5)
    assert pipeline_run_status_canceled

    # Check that terminate cannot be called again
    assert not dagster_instance.run_launcher.can_terminate(run_id=run.run_id)
    assert not dagster_instance.run_launcher.terminate(run_id=run.run_id)

    # Check for step failure and resource tear down
    expected_events_found = False
    start_time = datetime.datetime.now()
    while datetime.datetime.now() < start_time + timeout:
        step_failures_count = 0
        resource_tear_down_count = 0
        resource_init_count = 0
        termination_request_count = 0
        termination_success_count = 0
        event_records = dagster_instance.all_logs(run.run_id)
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
    key = "resource_termination_test/{}".format(run.run_id)
    assert s3.get_object(Bucket=bucket, Key=key)


def test_execute_on_celery_k8s_with_termination(  # pylint: disable=redefined-outer-name
    dagster_docker_image, dagster_instance, helm_namespace
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

    _test_termination(dagster_instance, run_config)


@pytest.fixture(scope="function")
def set_dagster_k8s_pipeline_run_namespace_env(helm_namespace):
    try:
        old_value = os.getenv("DAGSTER_K8S_PIPELINE_RUN_NAMESPACE")
        os.environ["DAGSTER_K8S_PIPELINE_RUN_NAMESPACE"] = helm_namespace
        yield
    finally:
        if old_value is not None:
            os.environ["DAGSTER_K8S_PIPELINE_RUN_NAMESPACE"] = old_value


def test_execute_on_celery_k8s_with_env_var_and_termination(  # pylint: disable=redefined-outer-name
    dagster_docker_image, dagster_instance, set_dagster_k8s_pipeline_run_namespace_env
):
    run_config = merge_dicts(
        merge_yamls(
            [
                os.path.join(get_test_project_environments_path(), "env_s3.yaml"),
            ]
        ),
        get_celery_engine_config(
            dagster_docker_image=dagster_docker_image,
            job_namespace={"env": "DAGSTER_K8S_PIPELINE_RUN_NAMESPACE"},
        ),
    )

    _test_termination(dagster_instance, run_config)


def test_execute_on_celery_k8s_with_hard_failure(  # pylint: disable=redefined-outer-name
    dagster_docker_image, dagster_instance, set_dagster_k8s_pipeline_run_namespace_env
):
    run_config = merge_dicts(
        merge_dicts(
            merge_yamls(
                [
                    os.path.join(get_test_project_environments_path(), "env_s3.yaml"),
                ]
            ),
            get_celery_engine_config(
                dagster_docker_image=dagster_docker_image,
                job_namespace={"env": "DAGSTER_K8S_PIPELINE_RUN_NAMESPACE"},
            ),
        ),
        {"solids": {"hard_fail_or_0": {"config": {"fail": True}}}},
    )

    pipeline_name = "hard_failer"
    run = create_run_for_test(
        dagster_instance,
        pipeline_name=pipeline_name,
        run_config=run_config,
        mode="default",
    )

    dagster_instance.launch_run(
        run.run_id,
        ReOriginatedExternalPipelineForTest(get_test_project_external_pipeline(pipeline_name)),
    )
    assert isinstance(dagster_instance.run_launcher, CeleryK8sRunLauncher)

    # Check that pipeline run is marked as failed
    pipeline_run_status_failure = False
    start_time = datetime.datetime.now()
    timeout = datetime.timedelta(0, 120)

    while datetime.datetime.now() < start_time + timeout:
        pipeline_run = dagster_instance.get_run_by_id(run.run_id)
        if pipeline_run.status == PipelineRunStatus.FAILURE:
            pipeline_run_status_failure = True
            break
        time.sleep(5)
    assert pipeline_run_status_failure

    # Check for step failure for hard_fail_or_0.compute
    start_time = datetime.datetime.now()
    step_failure_found = False
    while datetime.datetime.now() < start_time + timeout:
        event_records = dagster_instance.all_logs(run.run_id)
        for event_record in event_records:
            if event_record.dagster_event:
                if (
                    event_record.dagster_event.event_type == DagsterEventType.STEP_FAILURE
                    and event_record.dagster_event.step_key == "hard_fail_or_0"
                ):
                    step_failure_found = True
                    break
        time.sleep(5)
    assert step_failure_found
