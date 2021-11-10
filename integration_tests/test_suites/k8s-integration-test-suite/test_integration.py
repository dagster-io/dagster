import datetime
import os
import time

import pytest
from dagster import DagsterEventType, check
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.storage.tags import DOCKER_IMAGE_TAG
from dagster.core.test_utils import create_run_for_test
from dagster.utils import load_yaml_from_path, merge_dicts
from dagster.utils.yaml_utils import merge_yamls
from dagster_k8s.client import DagsterKubernetesClient
from dagster_k8s.launcher import K8sRunLauncher
from dagster_k8s.test import wait_for_job_and_get_raw_logs
from dagster_k8s.utils import wait_for_job
from dagster_k8s_test_infra.helm import TEST_AWS_CONFIGMAP_NAME
from dagster_k8s_test_infra.integration_utils import image_pull_policy
from dagster_test.test_project import (
    ReOriginatedExternalPipelineForTest,
    get_test_project_docker_image,
    get_test_project_environments_path,
    get_test_project_external_pipeline_hierarchy,
)


@pytest.mark.integration
def test_k8s_run_launcher_default(
    dagster_instance_for_k8s_run_launcher, helm_namespace_for_k8s_run_launcher
):
    # sanity check that we have a K8sRunLauncher
    check.inst(dagster_instance_for_k8s_run_launcher.run_launcher, K8sRunLauncher)
    pods = DagsterKubernetesClient.production_client().core_api.list_namespaced_pod(
        namespace=helm_namespace_for_k8s_run_launcher
    )
    celery_pod_names = [p.metadata.name for p in pods.items if "celery-workers" in p.metadata.name]
    check.invariant(not celery_pod_names)

    run_config = load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env.yaml"))
    pipeline_name = "demo_pipeline"
    tags = {"key": "value"}

    with get_test_project_external_pipeline_hierarchy(
        dagster_instance_for_k8s_run_launcher, pipeline_name
    ) as (
        workspace,
        location,
        _repo,
        external_pipeline,
    ):
        reoriginated_pipeline = ReOriginatedExternalPipelineForTest(external_pipeline)
        run = create_run_for_test(
            dagster_instance_for_k8s_run_launcher,
            pipeline_name=pipeline_name,
            run_config=run_config,
            tags=tags,
            mode="default",
            pipeline_snapshot=external_pipeline.pipeline_snapshot,
            execution_plan_snapshot=location.get_external_execution_plan(
                external_pipeline, run_config, "default", None, None
            ).execution_plan_snapshot,
            external_pipeline_origin=reoriginated_pipeline.get_external_origin(),
            pipeline_code_origin=reoriginated_pipeline.get_python_origin(),
        )
        dagster_instance_for_k8s_run_launcher.launch_run(run.run_id, workspace)

        result = wait_for_job_and_get_raw_logs(
            job_name="dagster-run-%s" % run.run_id, namespace=helm_namespace_for_k8s_run_launcher
        )

        assert "PIPELINE_SUCCESS" in result, "no match, result: {}".format(result)

        updated_run = dagster_instance_for_k8s_run_launcher.get_run_by_id(run.run_id)
        assert updated_run.tags[DOCKER_IMAGE_TAG] == get_test_project_docker_image()


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


def test_k8s_run_launcher_with_celery_executor_fails(
    dagster_docker_image, dagster_instance_for_k8s_run_launcher, helm_namespace_for_k8s_run_launcher
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
            job_namespace=helm_namespace_for_k8s_run_launcher,
        ),
    )

    pipeline_name = "demo_pipeline_celery"

    with get_test_project_external_pipeline_hierarchy(
        dagster_instance_for_k8s_run_launcher, pipeline_name
    ) as (
        workspace,
        location,
        _repo,
        external_pipeline,
    ):
        reoriginated_pipeline = ReOriginatedExternalPipelineForTest(external_pipeline)

        run = create_run_for_test(
            dagster_instance_for_k8s_run_launcher,
            pipeline_name=pipeline_name,
            run_config=run_config,
            mode="default",
            pipeline_snapshot=external_pipeline.pipeline_snapshot,
            execution_plan_snapshot=location.get_external_execution_plan(
                external_pipeline, run_config, "default", None, None
            ).execution_plan_snapshot,
            external_pipeline_origin=reoriginated_pipeline.get_external_origin(),
            pipeline_code_origin=reoriginated_pipeline.get_python_origin(),
        )
        dagster_instance_for_k8s_run_launcher.launch_run(run.run_id, workspace)

        timeout = datetime.timedelta(0, 120)

        found_pipeline_failure = False

        start_time = datetime.datetime.now()

        while datetime.datetime.now() < start_time + timeout:
            event_records = dagster_instance_for_k8s_run_launcher.all_logs(run.run_id)

            for event_record in event_records:
                if event_record.dagster_event:
                    if event_record.dagster_event.event_type == DagsterEventType.PIPELINE_FAILURE:
                        found_pipeline_failure = True

            if found_pipeline_failure:
                break

            time.sleep(5)

        assert found_pipeline_failure
        assert (
            dagster_instance_for_k8s_run_launcher.get_run_by_id(run.run_id).status
            == PipelineRunStatus.FAILURE
        )


@pytest.mark.integration
def test_failing_k8s_run_launcher(
    dagster_instance_for_k8s_run_launcher, helm_namespace_for_k8s_run_launcher
):
    run_config = {"blah blah this is wrong": {}}
    pipeline_name = "demo_pipeline"

    with get_test_project_external_pipeline_hierarchy(
        dagster_instance_for_k8s_run_launcher, pipeline_name
    ) as (
        workspace,
        location,
        _repo,
        external_pipeline,
    ):
        reoriginated_pipeline = ReOriginatedExternalPipelineForTest(external_pipeline)
        run = create_run_for_test(
            dagster_instance_for_k8s_run_launcher,
            pipeline_name=pipeline_name,
            run_config=run_config,
            pipeline_snapshot=external_pipeline.pipeline_snapshot,
            execution_plan_snapshot=location.get_external_execution_plan(
                external_pipeline,
                {
                    "solids": {
                        "multiply_the_word": {"config": {"factor": 0}, "inputs": {"word": "..."}}
                    }
                },
                "default",
                None,
                None,
            ).execution_plan_snapshot,
            external_pipeline_origin=reoriginated_pipeline.get_external_origin(),
            pipeline_code_origin=reoriginated_pipeline.get_python_origin(),
        )
        dagster_instance_for_k8s_run_launcher.launch_run(run.run_id, workspace)
        result = wait_for_job_and_get_raw_logs(
            job_name="dagster-run-%s" % run.run_id, namespace=helm_namespace_for_k8s_run_launcher
        )

        assert "PIPELINE_SUCCESS" not in result, "no match, result: {}".format(result)

        event_records = dagster_instance_for_k8s_run_launcher.all_logs(run.run_id)

        assert any(
            [
                'Received unexpected config entry "blah blah this is wrong"' in str(event)
                for event in event_records
            ]
        )
        assert any(
            ['Missing required config entry "solids"' in str(event) for event in event_records]
        )


@pytest.mark.integration
def test_k8s_run_launcher_terminate(
    dagster_instance_for_k8s_run_launcher, helm_namespace_for_k8s_run_launcher
):
    pipeline_name = "slow_pipeline"

    tags = {"key": "value"}
    run_config = load_yaml_from_path(
        os.path.join(get_test_project_environments_path(), "env_s3.yaml")
    )

    run_config = load_yaml_from_path(
        os.path.join(get_test_project_environments_path(), "env_s3.yaml")
    )

    with get_test_project_external_pipeline_hierarchy(
        dagster_instance_for_k8s_run_launcher, pipeline_name
    ) as (
        workspace,
        location,
        _repo,
        external_pipeline,
    ):
        reoriginated_pipeline = ReOriginatedExternalPipelineForTest(external_pipeline)
        run = create_run_for_test(
            dagster_instance_for_k8s_run_launcher,
            pipeline_name=pipeline_name,
            run_config=run_config,
            tags=tags,
            mode="default",
            pipeline_snapshot=external_pipeline.pipeline_snapshot,
            execution_plan_snapshot=location.get_external_execution_plan(
                external_pipeline, run_config, "default", None, None
            ).execution_plan_snapshot,
            external_pipeline_origin=reoriginated_pipeline.get_external_origin(),
            pipeline_code_origin=reoriginated_pipeline.get_python_origin(),
        )

        dagster_instance_for_k8s_run_launcher.launch_run(run.run_id, workspace)

        wait_for_job(
            job_name="dagster-run-%s" % run.run_id, namespace=helm_namespace_for_k8s_run_launcher
        )

        timeout = datetime.timedelta(0, 30)
        start_time = datetime.datetime.now()
        while datetime.datetime.now() < start_time + timeout:
            if dagster_instance_for_k8s_run_launcher.run_launcher.can_terminate(run_id=run.run_id):
                break
            time.sleep(5)

        assert dagster_instance_for_k8s_run_launcher.run_launcher.can_terminate(run_id=run.run_id)
        assert dagster_instance_for_k8s_run_launcher.run_launcher.terminate(run_id=run.run_id)

        start_time = datetime.datetime.now()
        pipeline_run = None
        while datetime.datetime.now() < start_time + timeout:
            pipeline_run = dagster_instance_for_k8s_run_launcher.get_run_by_id(run.run_id)
            if pipeline_run.status == PipelineRunStatus.CANCELED:
                break
            time.sleep(5)

        assert pipeline_run.status == PipelineRunStatus.CANCELED

        assert not dagster_instance_for_k8s_run_launcher.run_launcher.terminate(run_id=run.run_id)
