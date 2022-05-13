import re

from .client import (
    DEFAULT_JOB_POD_COUNT,
    DEFAULT_WAIT_BETWEEN_ATTEMPTS,
    DEFAULT_WAIT_TIMEOUT,
    DagsterKubernetesClient,
    WaitForPodState,
)


def sanitize_k8s_label(label_name: str):
    # Truncate too long label values to fit into 63-characters limit and avoid invalid characters.
    # https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#syntax-and-character-set
    label_name = label_name[:63]
    return re.sub(r"[^a-zA-Z0-9\-_\.]", "-", label_name).strip("-").strip("_")


def retrieve_pod_logs(pod_name, namespace):
    return DagsterKubernetesClient.production_client().retrieve_pod_logs(pod_name, namespace)


def get_pods_in_job(job_name, namespace):
    return DagsterKubernetesClient.production_client().get_pods_in_job(job_name, namespace)


def get_pod_names_in_job(job_name, namespace):
    return DagsterKubernetesClient.production_client().get_pod_names_in_job(job_name, namespace)


def delete_job(job_name, namespace):
    return DagsterKubernetesClient.production_client().delete_job(job_name, namespace)


def wait_for_job_success(
    job_name,
    namespace,
    instance=None,
    run_id=None,
    wait_timeout=DEFAULT_WAIT_TIMEOUT,
    wait_time_between_attempts=DEFAULT_WAIT_BETWEEN_ATTEMPTS,
    num_pods_to_wait_for=DEFAULT_JOB_POD_COUNT,
):
    return DagsterKubernetesClient.production_client().wait_for_job_success(
        job_name,
        namespace,
        instance,
        run_id,
        wait_timeout,
        wait_time_between_attempts,
        num_pods_to_wait_for,
    )


def wait_for_job(
    job_name,
    namespace,
    wait_timeout=DEFAULT_WAIT_TIMEOUT,
    wait_time_between_attempts=DEFAULT_WAIT_BETWEEN_ATTEMPTS,
):
    return DagsterKubernetesClient.production_client().wait_for_job(
        job_name=job_name,
        namespace=namespace,
        wait_timeout=wait_timeout,
        wait_time_between_attempts=wait_time_between_attempts,
    )


def wait_for_pod(
    pod_name,
    namespace,
    wait_for_state=WaitForPodState.Ready,
    wait_timeout=DEFAULT_WAIT_TIMEOUT,
    wait_time_between_attempts=DEFAULT_WAIT_BETWEEN_ATTEMPTS,
):
    return DagsterKubernetesClient.production_client().wait_for_pod(
        pod_name, namespace, wait_for_state, wait_timeout, wait_time_between_attempts
    )
