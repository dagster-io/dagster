import datetime
import json
import sys

import kubernetes
import pytest
from dagster_k8s.test import wait_for_job_and_get_raw_logs
from kubernetes.stream import stream
from marks import mark_user_code_deployment


# This test spins up a user code deployment, and then executes a launch pipeline command in the
# dagit pod to trigger a pipeline run
@mark_user_code_deployment
@pytest.mark.integration
@pytest.mark.skipif(sys.version_info < (3, 5), reason="Very slow on Python 2")
def test_execute_on_celery_k8s(  # pylint: disable=redefined-outer-name,unused-argument
    dagster_instance_for_user_deployments, helm_namespace_for_user_deployments,
):
    namespace = helm_namespace_for_user_deployments
    pipeline_name = 'demo_pipeline_celery'

    core_api = kubernetes.client.CoreV1Api()
    batch_api = kubernetes.client.BatchV1Api()

    # Get name for dagit pod
    pods = core_api.list_namespaced_pod(namespace=namespace)
    dagit_pod_list = list(filter(lambda item: 'dagit' in item.metadata.name, pods.items))
    assert len(dagit_pod_list) == 1
    dagit_pod = dagit_pod_list[0]
    dagit_pod_name = dagit_pod.metadata.name

    # Check that there are no run master jobs
    jobs = batch_api.list_namespaced_job(namespace=namespace)
    runmaster_job_list = list(filter(lambda item: 'dagster-run-' in item.metadata.name, jobs.items))
    assert len(runmaster_job_list) == 0

    run_config_dict = {
        'storage': {'s3': {'config': {'s3_bucket': 'dagster-scratch-80542c2'}}},
        'execution': {
            'celery-k8s': {
                'config': {
                    'image_pull_policy': "Always",
                    'env_config_maps': ["dagster-pipeline-env"],
                    'job_namespace': namespace,
                }
            }
        },
        'loggers': {'console': {'config': {'log_level': 'DEBUG'}}},
        'solids': {'multiply_the_word': {'inputs': {'word': 'bar'}, 'config': {'factor': 2}}},
    }
    run_config_json = json.dumps(run_config_dict)

    exec_command = [
        'dagster',
        'pipeline',
        'launch',
        '--repository',
        'demo_execution_repo',
        '--pipeline',
        pipeline_name,
        '--workspace',
        '/dagster-workspace/workspace.yaml',
        '--location',
        'user-code-deployment-1',
        '--config-json',
        run_config_json,
    ]

    stream(
        core_api.connect_get_namespaced_pod_exec,
        name=dagit_pod_name,
        namespace=namespace,
        command=exec_command,
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
        _preload_content=False,
    )

    runmaster_job_name = None
    timeout = datetime.timedelta(0, 90)
    start_time = datetime.datetime.now()
    while datetime.datetime.now() < start_time + timeout and not runmaster_job_name:
        jobs = batch_api.list_namespaced_job(namespace=namespace)
        runmaster_job_list = list(
            filter(lambda item: 'dagster-run-' in item.metadata.name, jobs.items)
        )
        if len(runmaster_job_list) > 0:
            runmaster_job_name = runmaster_job_list[0].metadata.name

    assert runmaster_job_name

    result = wait_for_job_and_get_raw_logs(job_name=runmaster_job_name, namespace=namespace)
    assert 'PIPELINE_SUCCESS' in result, 'no match, result: {}'.format(result)
