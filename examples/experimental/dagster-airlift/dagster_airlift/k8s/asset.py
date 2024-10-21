from typing import Any, Mapping, Optional, Sequence

from dagster import AssetExecutionContext, AssetSpec, Definitions, multi_asset
from dagster_k8s import PipesK8sClient


def k8s_pod_defs(
    specs: Sequence[AssetSpec],
    pod_spec: Mapping[str, Any],
    pod_metadata: Mapping[str, Any],
    load_incluster_config: bool = False,
    kube_context: Optional[str] = None,
    kubeconfig_file: Optional[str] = None,
) -> Definitions:
    """Define a set of assets which are materialized in a k8s pod.

    This is designed to be an equivalent to the KubernetesPodOperator in Airflow.
    The same non-airflow specific arguments are exposed here as in the operator, and their meaning is maintained.
    Under the hood, this is launching an ephemeral kubernetes pod using the :py:class:`dagster_k8s.PipesK8sClient`.

    Comparison of Airflow KubernetesPodOperator parameters to this function.

    Directly supported arguments:
    - in_cluster (named load_incluster_config here)
    - cluster_context (named kube_context here)
    - config_file (named kubeconfig_file here)

    Many arguments are supported indirectly via the pod_spec argument.
    - volumes: Volumes to be used by the Pod (key ['volumes'])
    - affinity: Node affinity/anti-affinity rules for the Pod (key ['affinity'])
    - node_selector: Node selection constraints for the Pod (key ['nodeSelector'])
    - hostnetwork: Enable host networking for the Pod (key ['hostNetwork'])
    - dns_config: DNS settings for the Pod (key ['dnsConfig'])
    - dnspolicy: DNS policy for the Pod (key ['dnsPolicy'])
    - hostname: Hostname of the Pod (key ['hostname'])
    - subdomain: Subdomain for the Pod (key ['subdomain'])
    - schedulername: Scheduler to be used for the Pod (key ['schedulerName'])
    - service_account_name: Service account to be used by the Pod (key ['serviceAccountName'])
    - priority_class_name: Priority class for the Pod (key ['priorityClassName'])
    - security_context: Security context for the entire Pod (key ['securityContext'])
    - tolerations: Tolerations for the Pod (key ['tolerations'])
    - image_pull_secrets: Secrets for pulling container images (key ['imagePullSecrets'])
    - termination_grace_period: Grace period for Pod termination (key ['terminationGracePeriodSeconds'])
    - active_deadline_seconds: Deadline for the Pod's execution (key ['activeDeadlineSeconds'])
    - host_aliases: Additional entries for the Pod's /etc/hosts (key ['hostAliases'])
    - init_containers: Initialization containers for the Pod (key ['initContainers'])
    The following arguments are supported under the nested ['containers'] key of the pod_spec argument:
    - image: Docker image for the container (key ['image'])
    - cmds: Entrypoint command for the container (key ['command'])
    - arguments: Arguments for the entrypoint command (key ['args'])
    - ports: List of ports to expose from the container (key ['ports'])
    - volume_mounts: List of volume mounts for the container (key ['volumeMounts'])
    - env_vars: Environment variables for the container (key ['env'])
    - env_from: List of sources to populate environment variables (key ['envFrom'])
    - image_pull_policy: Policy for pulling the container image (key ['imagePullPolicy'])
    - container_resources: Resource requirements for the container (key ['resources'])
    - container_security_context: Security context for the container (key ['securityContext'])
    - termination_message_policy: Policy for the termination message (key ['terminationMessagePolicy'])
    For a full list, see https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.26/#container-v1-core.
    The following arguments are supported under the pod_metadata argument, which configures the metadata of the pod:
    - name: ['name']
    - namespace: ['namespace']
    - labels: ['labels']
    - annotations: ['annotations']
    For a full list, see https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.26/#objectmeta-v1-meta.

    Example usage:
    .. code-block:: python
        k8s_pod_defs(
            specs=[AssetSpec("my_asset")],
            pod_spec_config={
                "containers": [
                    {
                        "name": "airflow-test-pod",
                        "image": "ubuntu:18.04",
                        "command": ["bash", "-cx"],
                        "args": ["sleep 100"],
                    }
                ]
            },
            pod_metadata={"name": "my-pod"},
            in_cluster=False,
            cluster_context="minikube",
        )

    """

    @multi_asset(specs=specs)
    def _k8s_multi_asset(context: AssetExecutionContext):
        return (
            PipesK8sClient(
                load_incluster_config=load_incluster_config,
                kubeconfig_file=kubeconfig_file,
                kube_context=kube_context,
            )
            .run(
                context=context.op_execution_context,
                base_pod_meta=pod_metadata,
                base_pod_spec=pod_spec,
            )
            .get_results()
        )

    return Definitions(assets=[_k8s_multi_asset])
