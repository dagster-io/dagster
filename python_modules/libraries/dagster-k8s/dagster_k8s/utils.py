from .client import (
    DEFAULT_JOB_POD_COUNT,
    DEFAULT_WAIT_BETWEEN_ATTEMPTS,
    DEFAULT_WAIT_TIMEOUT,
    DagsterKubernetesClient,
    WaitForPodState,
)


def retrieve_pod_logs(pod_name, namespace):
    return DagsterKubernetesClient.production_client().retrieve_pod_logs(pod_name, namespace)


def get_pod_names_in_job(job_name, namespace):
    return DagsterKubernetesClient.production_client().get_pod_names_in_job(job_name, namespace)


def wait_for_job_success(
    job_name,
    namespace,
    wait_timeout=DEFAULT_WAIT_TIMEOUT,
    wait_time_between_attempts=DEFAULT_WAIT_BETWEEN_ATTEMPTS,
    num_pods_to_wait_for=DEFAULT_JOB_POD_COUNT,
):
    return DagsterKubernetesClient.production_client().wait_for_job_success(
        job_name, namespace, wait_timeout, wait_time_between_attempts, num_pods_to_wait_for
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
