import time

import kubernetes
from dagster_k8s.client import DagsterKubernetesClient


def _wait_k8s_job_to_delete(
    api_client: DagsterKubernetesClient, job_name: str, namespace: str
) -> None:
    """Wait until Kubernetes job is deleted."""
    for _ in range(5):
        try:
            api_client.batch_api.read_namespaced_job_status(job_name, namespace)
            time.sleep(5)
        except kubernetes.client.rest.ApiException:
            return
