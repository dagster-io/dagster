from dagster import check
from dagster_k8s.utils import (
    get_pod_names_in_job,
    retrieve_pod_logs,
    wait_for_job,
    wait_for_job_success,
)


def wait_for_job_ready(job_name, namespace):
    """Wait for a dagster-k8s job to be ready"""
    check.str_param(job_name, "job_name")
    check.str_param(namespace, "namespace")

    wait_for_job(job_name=job_name, namespace=namespace)


def wait_for_job_and_get_raw_logs(job_name, namespace, wait_timeout=300):
    """Wait for a dagster-k8s job to complete, ensure it launched only one pod,
    and then grab the logs from the pod it launched.

    wait_timeout: default 5 minutes
    """
    check.str_param(job_name, "job_name")
    check.str_param(namespace, "namespace")

    wait_for_job_success(job_name, namespace=namespace, wait_timeout=wait_timeout)

    pod_names = get_pod_names_in_job(job_name, namespace)

    assert len(pod_names) == 1

    pod_name = pod_names[0]

    return retrieve_pod_logs(pod_name, namespace=namespace)
