import datetime
import json

import kubernetes
import pytest
from dagster_k8s.test import wait_for_job_and_get_raw_logs
from dagster_k8s_test_infra.integration_utils import image_pull_policy
from kubernetes.stream import stream
from marks import mark_user_code_deployment_subchart


@mark_user_code_deployment_subchart
@pytest.mark.integration
def test_execute_on_celery_k8s_subchart_disabled(  # pylint: disable=redefined-outer-name,unused-argument
    dagster_instance_for_user_deployments_subchart_disabled,
    helm_namespace_for_user_deployments_subchart_disabled,
):
    namespace = helm_namespace_for_user_deployments_subchart_disabled
    job_name = "demo_job_celery"

    core_api = kubernetes.client.CoreV1Api()
    batch_api = kubernetes.client.BatchV1Api()

    # Get name for dagit pod
    pods = core_api.list_namespaced_pod(namespace=namespace)
    dagit_pod_list = list(filter(lambda item: "dagit" in item.metadata.name, pods.items))
    assert len(dagit_pod_list) == 1
    dagit_pod = dagit_pod_list[0]
    dagit_pod_name = dagit_pod.metadata.name

    # Check that there are no run master jobs
    jobs = batch_api.list_namespaced_job(namespace=namespace)
    runmaster_job_list = list(filter(lambda item: "dagster-run-" in item.metadata.name, jobs.items))
    assert len(runmaster_job_list) == 0

    run_config_dict = {
        "resources": {"io_manager": {"config": {"s3_bucket": "dagster-scratch-80542c2"}}},
        "execution": {
            "config": {
                "image_pull_policy": image_pull_policy(),
                "job_namespace": namespace,
            }
        },
        "loggers": {"console": {"config": {"log_level": "DEBUG"}}},
        "ops": {"multiply_the_word": {"inputs": {"word": "bar"}, "config": {"factor": 2}}},
    }
    run_config_json = json.dumps(run_config_dict)

    exec_command = [
        "dagster",
        "job",
        "launch",
        "--repository",
        "demo_execution_repo",
        "--job",
        job_name,
        "--workspace",
        "/dagster-workspace/workspace.yaml",
        "--location",
        "user-code-deployment-1",
        "--config-json",
        run_config_json,
    ]

    resp = stream(
        core_api.connect_get_namespaced_pod_exec,
        name=dagit_pod_name,
        namespace=namespace,
        command=exec_command,
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
    )
    print("Response: ")  # noqa: T201
    print(resp)  # noqa: T201

    runmaster_job_name = None
    timeout = datetime.timedelta(0, 90)
    start_time = datetime.datetime.now()
    while datetime.datetime.now() < start_time + timeout and not runmaster_job_name:
        jobs = batch_api.list_namespaced_job(namespace=namespace)
        runmaster_job_list = list(
            filter(lambda item: "dagster-run-" in item.metadata.name, jobs.items)
        )
        if len(runmaster_job_list) > 0:
            runmaster_job_name = runmaster_job_list[0].metadata.name

    assert runmaster_job_name

    result = wait_for_job_and_get_raw_logs(
        job_name=runmaster_job_name, namespace=namespace, wait_timeout=450
    )
    assert "PIPELINE_SUCCESS" in result, "no match, result: {}".format(result)
