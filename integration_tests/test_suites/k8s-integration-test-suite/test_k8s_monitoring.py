import os
import time

import pytest
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import create_run_for_test, poll_for_finished_run
from dagster.utils import load_yaml_from_path, merge_dicts
from dagster_k8s.job import get_job_name_from_run_id
from dagster_k8s.utils import delete_job
from dagster_k8s_test_infra.helm import TEST_AWS_CONFIGMAP_NAME
from dagster_k8s_test_infra.integration_utils import image_pull_policy
from dagster_test.test_project import (
    IS_BUILDKITE,
    ReOriginatedExternalPipelineForTest,
    get_test_project_environments_path,
    get_test_project_external_pipeline_hierarchy,
)


def log_run_events(instance, run_id):
    for log in instance.all_logs(run_id):
        print(str(log) + "\n")  # pylint: disable=print-call


@pytest.mark.integration
def test_k8s_run_monitoring(
    dagster_instance_for_k8s_run_launcher,
    helm_namespace_for_k8s_run_launcher,
    dagster_docker_image,
):
    run_config = merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "execution": {
                "k8s": {
                    "config": {
                        "job_namespace": helm_namespace_for_k8s_run_launcher,
                        "image_pull_policy": image_pull_policy(),
                        "env_config_maps": ["dagster-pipeline-env"]
                        + ([TEST_AWS_CONFIGMAP_NAME] if not IS_BUILDKITE else []),
                    }
                }
            },
        },
    )
    _launch_run_and_wait_for_resume(
        run_config,
        dagster_instance_for_k8s_run_launcher,
        helm_namespace_for_k8s_run_launcher,
        dagster_docker_image=dagster_docker_image,
    )


def _launch_run_and_wait_for_resume(
    run_config, instance, namespace, pipeline_name="slow_pipeline", dagster_docker_image=None,
):
    tags = {"key": "value"}

    with get_test_project_external_pipeline_hierarchy(instance, pipeline_name) as (
        workspace,
        location,
        _repo,
        external_pipeline,
    ):
        reoriginated_pipeline = ReOriginatedExternalPipelineForTest(
            external_pipeline, container_image=dagster_docker_image
        )
        run = create_run_for_test(
            instance,
            pipeline_name=pipeline_name,
            run_config=run_config,
            tags=tags,
            mode="k8s",
            pipeline_snapshot=external_pipeline.pipeline_snapshot,
            execution_plan_snapshot=location.get_external_execution_plan(
                external_pipeline, run_config, "k8s", None, None
            ).execution_plan_snapshot,
            external_pipeline_origin=reoriginated_pipeline.get_external_origin(),
            pipeline_code_origin=reoriginated_pipeline.get_python_origin(),
        )

        try:
            instance.launch_run(run.run_id, workspace)

            start_time = time.time()
            while time.time() - start_time < 60:
                run = instance.get_run_by_id(run.run_id)
                if run.status == PipelineRunStatus.STARTED:
                    break
                assert run.status == PipelineRunStatus.STARTING
                time.sleep(1)

            time.sleep(5)
            assert delete_job(get_job_name_from_run_id(run.run_id), namespace)

            poll_for_finished_run(instance, run.run_id, timeout=120)
            assert instance.get_run_by_id(run.run_id).status == PipelineRunStatus.SUCCESS
        finally:
            log_run_events(instance, run.run_id)
