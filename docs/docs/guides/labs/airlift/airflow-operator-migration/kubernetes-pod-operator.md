---
description: Migrating an Airflow `KubernetesPodOperator` to Dagster.
sidebar_position: 400
title: Migrating an Airflow KubernetesPodOperator to Dagster
---

The `KubernetesPodOperator` in Apache Airflow allows you to execute containerized tasks within Kubernetes pods as part of your data pipelines.

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/kubernetes_pod_operator.py" />

## Dagster equivalent

The Dagster equivalent to the `KubernetesPodOperator` is to use the <PyObject section="libraries" object="PipesK8sClient" module="dagster_k8s"/> to execute a task within a Kubernetes pod:

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/using_k8s_pipes.py" />

## Migrating the operator

To migrate the operator, you will need to:

1. Ensure that your Dagster deployment has access to the Kubernetes cluster.
2. Write an <PyObject section="assets" object="asset" module="dagster"/> that executes the task within a Kubernetes pod using the <PyObject section="libraries" object="PipesK8sClient" module="dagster_k8s"/>.
3. Use `dagster-airlift` to proxy execution of the original task to Dagster.

### Step 1: Ensure access to the Kubernetes cluster

First, you need to ensure that your Dagster deployment has access to the Kubernetes cluster where you want to run your tasks. The <PyObject section="libraries" object="PipesK8sClient" module="dagster_k8s"/> accepts `kubeconfig` and `kubecontext`, and `env` arguments to configure the Kubernetes client.

Here's an example of what this might look like when configuring the client to access an EKS cluster:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/k8s_eks_fake_example.py"
  startAfter="start_client"
  endBefore="end_client"
/>

### Step 2: Write an asset that executes the task within a Kubernetes pod

Once you have access to the Kubernetes cluster, you can write an <PyObject section="assets" object="asset" module="dagster"/> that executes the task within a Kubernetes pod using the <PyObject section="libraries" object="PipesK8sClient" module="dagster_k8s"/>. Unlike the `KubernetesPodOperator`, the PipesK8sClient allows you to define the pod spec directly in your Python code. For example:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/k8s_eks_fake_example.py"
  startAfter="start_asset"
  endBefore="end_asset"
/>

In the [parameter comparison](#parameter-comparison) section of this guide, you'll find a reference for mapping `KubernetesPodOperator` parameters to `PipesK8sClient` parameters.

For more information on the full capabilities of the `PipesK8sClient`, see the "[Build pipelines with Kubernetes](/guides/build/external-pipelines/kubernetes-pipeline)".

### Step 3: Using dagster-airlift to proxy execution

Finally, you can use `dagster-airlift` to proxy the execution of the original task to Dagster. For more information, see "[Migrate from Airflow to Dagster at the task level](/guides/migrate/airflow-to-dagster/task-level-migration)".

## Parameter comparison

Here's a comparison of the parameters between the Airflow `KubernetesPodOperator` and the Dagster `PipesK8sClient`.

### Directly supported arguments

| `KubernetesPodOperator` argument | `PipesK8sClient` argument |
|----------------------------------|---------------------------|
| `in_cluster` | `load_incluster_config` |
| `cluster_context` | `kube_context` |
| `config_file` | `kubeconfig_file` |

### Indirectly support arguments

Many arguments are supported indirectly as keys passed to the `base_pod_spec` argument:

| `KubernetesPodOperator` argument | `PipesK8sClient` key (under `base_pod_spec` argument) | Description |
|----------------------------------|--------------------------------------------------|-------------|
| `volumes` | `volumes` | Volumes to be used by the Pod |
| `affinity` | `affinity` | Node affinity/anti-affinity rules for the Pod |
| `node_selector` | `nodeSelector` | Node selection constraints for the Pod |
|  `hostnetwork` | `hostNetwork` | Enable host networking for the Pod |
| `dns_config` | `dnsConfig` | DNS settings for the Pod |
|  `dnspolicy` | `dnsPolicy` | DNS policy for the Pod |
| `hostname` | `hostname` | Hostname of the Pod |
| `subdomain` | `subdomain` | Subdomain for the Pod |
| `schedulername` | `schedulerName` | Scheduler to be used for the Pod |
| `service_account_name` | `serviceAccountName` | Service account to be used by the Pod |
| `priority_class_name` | `priorityClassName` | Priority class for the Pod |
| `security_context` | `securityContext` | Security context for the entire Pod |
| `tolerations` | `tolerations` | Tolerations for the Pod |
| `image_pull_secrets` | `imagePullSecrets` | Secrets for pulling container images |
| `termination_grace_period` | `terminationGracePeriodSeconds` | Grace period for Pod termination |
| `active_deadline_seconds` | `activeDeadlineSeconds` | Deadline for the Pod's execution |
| `host_aliases` | `hostAliases` | Additional entries for the Pod's `/etc/hosts` |
| `init_containers` | `initContainers` | Initialization containers for the Pod |

The following arguments are supported under the nested `containers` key of the `base_pod_spec` argument of the `PipesK8sClient`:

| `KubernetesPodOperator` argument | `PipesK8sClient` key (under `base_pod_spec` > `containers` argument) | Description |
|----------------------------------|-------------------------------------|------------------|
| `image` |  `image`| Docker image for the container |
| `cmds` | `command` | Entrypoint command for the container |
| `arguments` | `args` | Arguments for the entrypoint command |
| `ports` | `ports` | List of ports to expose from the container |
| `volume_mounts` | `volumeMounts` | List of volume mounts for the container |
| `env_vars` | `env` | Environment variables for the container |
| `env_from` | `envFrom` | List of sources to populate environment variables |
| `image_pull_policy` | `imagePullPolicy` | Policy for pulling the container image |
| `container_resources` | `resources` | Resource requirements for the container |
| `container_security_context` | `securityContext` | Security context for the container |
| `termination_message_policy` |  `terminationMessagePolicy` | Policy for the termination message |

For a full list, see the [Kubernetes container spec documentation](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.26/#container-v1-core).

The following arguments are supported under the `base_pod_meta` argument, which configures the metadata of the pod:

| `KubernetesPodOperator` argument | `PipesK8sClient` key (under `base_pod_meta` argument) |
|--------|--------|
| `name` | `name` |
| `namespace` | `namespace` |
| `labels` | `labels` |
| `annotations` | `annotations` |

For a full list, see the [Kubernetes objectmeta spec documentation](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.26/#objectmeta-v1-meta).
