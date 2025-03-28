---
title: 'Migrating an Airflow KubernetesPodOperator to Dagster'
sidebar_position: 400
---

In this page, we'll explain migrating an Airflow `KubernetesPodOperator` to Dagster.

## About the Airflow KubernetesPodOperator

The KubernetesPodOperator in Apache Airflow enables users to execute containerized tasks within Kubernetes pods as part of their data pipelines.

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/kubernetes_pod_operator.py" />

## Dagster equivalent

The Dagster equivalent is to use the <PyObject section="libraries" object="PipesK8sClient" module="dagster_k8s"/> to execute a task within a Kubernetes pod.

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/using_k8s_pipes.py" />

## Migrating the operator

Migrating the operator breaks down into a few steps:

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

### Step 2: Writing an asset that executes the task within a Kubernetes pod

Once you have access to the Kubernetes cluster, you can write an asset that executes the task within a Kubernetes pod using the <PyObject section="libraries" object="PipesK8sClient" module="dagster_k8s"/>. In comparison to the KubernetesPodOperator, the PipesK8sClient allows you to define the pod spec directly in your Python code.

In the [parameter comparison](#parameter-comparison) section of this doc, you'll find a detailed comparison describing how to map the KubernetesPodOperator parameters to the PipesK8sClient parameters.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/k8s_eks_fake_example.py"
  startAfter="start_asset"
  endBefore="end_asset"
/>

This is just a snippet of what the PipesK8sClient can do. Take a look at our full guide on the [dagster-k8s PipesK8sClient](/guides/build/external-pipelines/kubernetes-pipeline) for more information.

### Step 3: Using dagster-airlift to proxy execution

Finally, you can use `dagster-airlift` to proxy the execution of the original task to Dagster. For more information, see "[Migrate from Airflow to Dagster at the task level](../task-level-migration/)".

## Parameter comparison

Here's a comparison of the parameters between the KubernetesPodOperator and the PipesK8sClient: Directly supported arguments:

- in_cluster (named load_incluster_config in the PipesK8sClient)
- cluster_context (named kube_context in the PipesK8sClient)
- config_file (named kubeconfig_file in the PipesK8sClient)

Many arguments are supported indirectly via the `base_pod_spec` argument.

- volumes: Volumes to be used by the Pod (key `volumes`)
- affinity: Node affinity/anti-affinity rules for the Pod (key `affinity`)
- node_selector: Node selection constraints for the Pod (key `nodeSelector`)
- hostnetwork: Enable host networking for the Pod (key `hostNetwork`)
- dns_config: DNS settings for the Pod (key `dnsConfig`)
- dnspolicy: DNS policy for the Pod (key `dnsPolicy`)
- hostname: Hostname of the Pod (key `hostname`)
- subdomain: Subdomain for the Pod (key `subdomain`)
- schedulername: Scheduler to be used for the Pod (key `schedulerName`)
- service_account_name: Service account to be used by the Pod (key `serviceAccountName`)
- priority_class_name: Priority class for the Pod (key `priorityClassName`)
- security_context: Security context for the entire Pod (key `securityContext`)
- tolerations: Tolerations for the Pod (key `tolerations`)
- image_pull_secrets: Secrets for pulling container images (key `imagePullSecrets`)
- termination_grace_period: Grace period for Pod termination (key `terminationGracePeriodSeconds`)
- active_deadline_seconds: Deadline for the Pod's execution (key `activeDeadlineSeconds`)
- host_aliases: Additional entries for the Pod's /etc/hosts (key `hostAliases`)
- init_containers: Initialization containers for the Pod (key `initContainers`)

The following arguments are supported under the nested `containers` key of the `base_pod_spec` argument of the PipesK8sClient:

- image: Docker image for the container (key 'image')
- cmds: Entrypoint command for the container (key `command`)
- arguments: Arguments for the entrypoint command (key `args`)
- ports: List of ports to expose from the container (key `ports`)
- volume_mounts: List of volume mounts for the container (key `volumeMounts`)
- env_vars: Environment variables for the container (key `env`)
- env_from: List of sources to populate environment variables (key `envFrom`)
- image_pull_policy: Policy for pulling the container image (key `imagePullPolicy`)
- container_resources: Resource requirements for the container (key `resources`)
- container_security_context: Security context for the container (key `securityContext`)
- termination_message_policy: Policy for the termination message (key `terminationMessagePolicy`)

For a full list, see the [kubernetes container spec documentation](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.26/#container-v1-core). The following arguments are supported under the `base_pod_meta` argument, which configures the metadata of the pod:

- name: `name`
- namespace: `namespace`
- labels: `labels`
- annotations: `annotations`

For a full list, see the [kubernetes objectmeta spec documentation](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.26/#objectmeta-v1-meta).
