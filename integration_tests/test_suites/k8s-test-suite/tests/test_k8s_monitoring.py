import json
import os
import time

import pytest
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.test_utils import poll_for_finished_run
from dagster._utils.merger import merge_dicts
from dagster._utils.yaml_utils import load_yaml_from_path
from dagster_k8s.client import DagsterKubernetesClient
from dagster_k8s.job import get_job_name_from_run_id
from dagster_k8s_test_infra.integration_utils import image_pull_policy, launch_run_over_graphql
from dagster_test.test_project import get_test_project_environments_path


def log_run_events(instance, run_id):
    for log in instance.all_logs(run_id):
        print(str(log) + "\n")  # noqa: T201


@pytest.mark.integration
def test_k8s_run_monitoring_startup_fail(
    dagster_instance_for_k8s_run_launcher,
    user_code_namespace_for_k8s_run_launcher,
    webserver_url_for_k8s_run_launcher,
):
    run_config = merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "execution": {
                "config": {
                    "job_namespace": user_code_namespace_for_k8s_run_launcher,
                    "image_pull_policy": image_pull_policy(),
                    "env_config_maps": ["non-existent-config-map"],
                }
            }
        },
    )
    run_id = None
    try:
        run_id = launch_run_over_graphql(
            webserver_url_for_k8s_run_launcher,
            run_config=run_config,
            job_name="slow_job_k8s",
            tags={
                "dagster-k8s/config": json.dumps(
                    {
                        "container_config": {
                            "env_from": [{"config_map_ref": {"name": "non-existent-config-map"}}]
                        }
                    }
                )
            },
        )

        poll_for_finished_run(dagster_instance_for_k8s_run_launcher, run_id, timeout=120)
        assert (
            dagster_instance_for_k8s_run_launcher.get_run_by_id(run_id).status
            == DagsterRunStatus.FAILURE
        )
    finally:
        if run_id:
            log_run_events(dagster_instance_for_k8s_run_launcher, run_id)


@pytest.mark.integration
def test_k8s_run_monitoring_resume(
    dagster_instance_for_k8s_run_launcher,
    user_code_namespace_for_k8s_run_launcher,
    webserver_url_for_k8s_run_launcher,
):
    run_config = merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "execution": {
                "config": {
                    "job_namespace": user_code_namespace_for_k8s_run_launcher,
                    "image_pull_policy": image_pull_policy(),
                }
            },
        },
    )
    _launch_run_and_wait_for_resume(
        webserver_url_for_k8s_run_launcher,
        run_config,
        dagster_instance_for_k8s_run_launcher,
        user_code_namespace_for_k8s_run_launcher,
    )


def _launch_run_and_wait_for_resume(
    webserver_url_for_k8s_run_launcher,
    run_config,
    instance,
    namespace,
    job_name="slow_job_k8s",
):
    run_id = None

    try:
        run_id = launch_run_over_graphql(
            webserver_url_for_k8s_run_launcher,
            run_config=run_config,
            job_name=job_name,
        )

        start_time = time.time()
        while True:
            assert time.time() - start_time < 60, "Timed out waiting for run to start"
            run = instance.get_run_by_id(run_id)
            if run.status == DagsterRunStatus.STARTED:
                break
            assert run.status == DagsterRunStatus.STARTING
            time.sleep(1)

        time.sleep(5)
        assert DagsterKubernetesClient.production_client().delete_job(
            get_job_name_from_run_id(run_id), namespace
        )

        poll_for_finished_run(instance, run_id, timeout=120)
        assert instance.get_run_by_id(run_id).status == DagsterRunStatus.SUCCESS
    finally:
        if run_id:
            log_run_events(instance, run_id)
