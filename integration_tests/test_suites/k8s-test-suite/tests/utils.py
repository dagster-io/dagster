import time

import kubernetes
import kubernetes.client.rest
from dagster_k8s.client import DagsterKubernetesClient

# Pin to a non-:latest tag so kubelet defaults imagePullPolicy to IfNotPresent
# and uses the copy pre-loaded into the kind cluster (see conftest), avoiding
# docker.io flakes at test time.
BUSYBOX_IMAGE = "busybox:1.37.0"


def _wait_k8s_job_to_delete(
    api_client: DagsterKubernetesClient, job_name: str, namespace: str
) -> None:
    """Wait until Kubernetes job is deleted."""
    for _ in range(12):
        try:
            api_client.batch_api.read_namespaced_job_status(job_name, namespace)
            time.sleep(5)
        except kubernetes.client.rest.ApiException:
            return
