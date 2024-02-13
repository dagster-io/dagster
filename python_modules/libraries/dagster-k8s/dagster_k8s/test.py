from dagster_k8s.client import DagsterKubernetesClient


def wait_for_job_and_get_raw_logs(
    job_name: str,
    namespace: str,
    wait_timeout: int = 300,
):
    """Wait for a dagster-k8s job to complete, ensure it launched only one pod,
    and then grab the logs from the pod it launched.

    wait_timeout: default 5 minutes
    """
    client = DagsterKubernetesClient.production_client()

    client.wait_for_job_success(job_name, namespace=namespace, wait_timeout=wait_timeout)

    pod_names = client.get_pod_names_in_job(job_name, namespace)

    assert len(pod_names) == 1

    pod_name = pod_names[0]

    return client.retrieve_pod_logs(pod_name, namespace=namespace)
