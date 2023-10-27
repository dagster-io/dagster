# pylint doesn't know about pytest fixtures


import os
import time

from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.test_utils import poll_for_finished_run
from dagster._utils.merger import merge_dicts
from dagster._utils.yaml_utils import merge_yamls
from dagster_k8s.client import DagsterKubernetesClient
from dagster_k8s.job import get_job_name_from_run_id
from dagster_k8s_test_infra.integration_utils import image_pull_policy, launch_run_over_graphql
from dagster_test.test_project import get_test_project_environments_path
from marks import mark_monitoring

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


def log_run_events(instance, run_id):
    for log in instance.all_logs(run_id):
        print(str(log) + "\n")  # noqa: T201


def get_celery_job_engine_config(dagster_docker_image, job_namespace=None):
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
                (
                    {
                        "job_namespace": job_namespace,
                    }
                    if job_namespace
                    else {}
                ),
                {
                    "image_pull_policy": image_pull_policy(),
                },
            )
        },
    }


def get_failing_celery_job_engine_config(dagster_docker_image, job_namespace):
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
                    "env_config_maps": ["non-existent-config-map"],
                },
            )
        },
    }


@mark_monitoring
def test_run_monitoring_fails_on_interrupt(
    dagster_docker_image, dagster_instance, helm_namespace, webserver_url
):
    run_config = merge_dicts(
        merge_yamls(
            [
                os.path.join(get_test_project_environments_path(), "env.yaml"),
                os.path.join(get_test_project_environments_path(), "env_s3.yaml"),
            ]
        ),
        get_celery_job_engine_config(dagster_docker_image=dagster_docker_image),
    )

    job_name = "demo_job_celery_k8s"

    try:
        run_id = launch_run_over_graphql(webserver_url, run_config=run_config, job_name=job_name)
        start_time = time.time()
        while time.time() - start_time < 60:
            run = dagster_instance.get_run_by_id(run_id)
            if run.status == DagsterRunStatus.STARTED:
                break
            assert run.status == DagsterRunStatus.STARTING
            time.sleep(1)

        assert DagsterKubernetesClient.production_client().delete_job(
            get_job_name_from_run_id(run_id), helm_namespace
        )
        poll_for_finished_run(dagster_instance, run.run_id, timeout=120)
        assert dagster_instance.get_run_by_id(run_id).status == DagsterRunStatus.FAILURE
    finally:
        log_run_events(dagster_instance, run_id)


@mark_monitoring
def test_run_monitoring_startup_fail(
    dagster_docker_image, dagster_instance, helm_namespace, webserver_url
):
    run_config = merge_dicts(
        merge_yamls(
            [
                os.path.join(get_test_project_environments_path(), "env.yaml"),
                os.path.join(get_test_project_environments_path(), "env_s3.yaml"),
            ]
        ),
        get_failing_celery_job_engine_config(
            dagster_docker_image=dagster_docker_image, job_namespace=helm_namespace
        ),
    )

    job_name = "demo_job_celery_k8s"

    try:
        run_id = launch_run_over_graphql(webserver_url, run_config=run_config, job_name=job_name)
        start_time = time.time()
        while time.time() - start_time < 60:
            run = dagster_instance.get_run_by_id(run_id)
            if run.status == DagsterRunStatus.STARTED:
                break
            assert run.status == DagsterRunStatus.STARTING
            time.sleep(1)

        assert DagsterKubernetesClient.production_client().delete_job(
            get_job_name_from_run_id(run_id), helm_namespace
        )
        poll_for_finished_run(dagster_instance, run.run_id, timeout=120)
        assert dagster_instance.get_run_by_id(run_id).status == DagsterRunStatus.FAILURE
    finally:
        log_run_events(dagster_instance, run_id)
