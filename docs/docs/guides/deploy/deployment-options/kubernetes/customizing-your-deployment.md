---
title: "Customizing your Kubernetes deployment"
description: This section covers common ways to customize your Dagster Kubernetes deployment.
sidebar_position: 200
---

This guide covers common ways to customize your Dagster Helm deployment.

## Specifying custom Kubernetes configuration

Dagster allows you to pass custom configuration to the Kubernetes Jobs and Pods created by Dagster during execution.

### Instance-level Kubernetes Configuration

If your instance is using the <PyObject section="libraries" module="dagster_k8s" object="K8sRunLauncher" />, you can configure custom configuration for every run launched by Dagster by setting the `k8sRunLauncher.runK8sConfig` dictionary in the Helm chart.

`k8sRunLauncher.runK8sConfig` is a dictionary with the following keys:

- `containerConfig`: The Pod's container
- `podSpecConfig`: The Pod's PodSpec
- `podTemplateSpecMetadata`: The Pod's Metadata
- `jobSpecConfig`: The Job's JobSpec
- `jobMetadata`: The Job's Metadata

Refer to the [Kubernetes documentation](https://kubernetes.io/docs/home/) for more information about containers, Pod Specs, etc.

The value for each of these keys is a dictionary with the YAML configuration for the underlying Kubernetes object. The Kubernetes object fields can be configured using either snake case (for example, `volume_mounts`) or camel case (`volumeMounts`). For example:

<CodeExample path="docs_snippets/docs_snippets/deploying/kubernetes/run_k8s_config.yaml" />

If your Dagster job is configured with the <PyObject section="libraries" module="dagster_k8s" object="k8s_job_executor" /> that runs each step in its own pod, configuration that you set in `runK8sConfig` will also be propagated to the pods that are created for each step, unless that step's configuration is overridden using one of the methods below.

### Per-job Kubernetes configuration

If your instance is using the <PyObject section="libraries" module="dagster_k8s" object="K8sRunLauncher" /> or <PyObject section="libraries" module="dagster_celery_k8s" object="CeleryK8sRunLauncher" />, you can use the `dagster-k8s/config` tag on a Dagster job to pass custom configuration to the Kubernetes Jobs and Pods created by Dagster for that job.

`dagster-k8s/config` is a dictionary with the following keys:

- `container_config`: The Pod's Container
- `pod_spec_config`: The Pod's PodSpec
- `pod_template_spec_metadata`: The Pod's Metadata
- `job_spec_config`: The Job's JobSpec
- `job_metadata`: The Job's Metadata

Refer to the [Kubernetes documentation](https://kubernetes.io/docs/home/) for more information about containers, Pod Specs, etc.

The value for each of these keys is a dictionary with the YAML configuration for the underlying Kubernetes object. The Kubernetes object fields can be configured using either snake case (for example, `volume_mounts`) or camel case (`volumeMounts`). For example:

<CodeExample path="docs_snippets/docs_snippets/deploying/kubernetes/k8s_config_tag_job.py" startAfter="start_k8s_config" endBefore="end_k8s_config" />

Other run launchers will ignore the `dagster-k8s/config` tag.

The default [executor](/guides/operate/run-executors) - <PyObject section="execution" module="dagster" object="multi_or_in_process_executor" /> - will run each job in its own pod, executing each step in an individual process. If your Dagster job produces assets which have a short compute time (compared to the step overhead time), consider avoiding the step process creation cost by using the <PyObject section="execution" module="dagster" object="in_process_executor" /> executor, which runs each step serially in a single process. This can be especially useful where parallelism is obtained through a <PyObject section="partitions" module="dagster" object="PartitionsDefinition" /> and is unnecessary within the job.

For this use-case, the <PyObject section="execution" module="dagster" object="in_process_executor" /> is more efficient than running each step in its own process. The <PyObject section="libraries" module="dagster_k8s" object="k8s_job_executor" /> is contraindicated, as the delay of scheduling and starting up a new Dagster pod to execute every step would significantly slow down overall execution time.

### Kubernetes configuration on every step in a run

If your Dagster job is configured with the <PyObject section="libraries" module="dagster_k8s" object="k8s_job_executor" /> that runs each step in its own pod, configuration that you set on a job using the `dagster-k8s/config` tag will _not_ be propagated to any of those step pods. Use the `step_k8s_config` field on the executor to control the Kubernetes configuration for every step pod.

`step_k8s_config` is a dictionary with the following keys:

- `container_config`: The Pod's Container
- `pod_spec_config`: The Pod's PodSpec
- `pod_template_spec_metadata`: The Pod's Metadata
- `job_spec_config`: The Job's JobSpec
- `job_metadata`: The Job's Metadata

Refer to the [Kubernetes documentation](https://kubernetes.io/docs/home/) for more information about containers, Pod Specs, etc.

The value for each of these keys is a dictionary with the YAML configuration for the underlying Kubernetes object. The Kubernetes object fields can be configured using either snake case (for example, `volume_mounts`) or camel case (`volumeMounts`). For example:

<CodeExample path="docs_snippets/docs_snippets/deploying/kubernetes/step_k8s_config.py" startAfter="start_step_k8s_config" endBefore="end_step_k8s_config" />

### Kubernetes configuration on individual steps in a run

If your Dagster job is configured with the <PyObject section="libraries" module="dagster_k8s" object="k8s_job_executor" /> or <PyObject section="libraries" module="dagster_celery_k8s" object="celery_k8s_job_executor" /> that run each step in its own Kubernetes pod, you can use the `dagster-k8s/config` tag on a Dagster op to control the Kubernetes configuration for that specific op.

As above when used on jobs, `dagster-k8s/config` is a dictionary with the following keys:

- `container_config`: The Pod's Container
- `pod_spec_config`: The Pod's PodSpec
- `pod_template_spec_metadata`: The Pod's Metadata
- `job_spec_config`: The Job's JobSpec
- `job_metadata`: The Job's Metadata

Refer to the [Kubernetes documentation](https://kubernetes.io/docs/home/) for more information about containers, Pod Specs, etc.

The value for each of these keys is a dictionary with the YAML configuration for the underlying Kubernetes object. The Kubernetes object fields can be configured using either snake case (for example, `volume_mounts`) or camel case (`volumeMounts`). For example:

For example, for an asset:

<CodeExample path="docs_snippets/docs_snippets/deploying/kubernetes/k8s_config_tag_asset.py" startAfter="start_k8s_config" endBefore="end_k8s_config" />

or an op:

<CodeExample path="docs_snippets/docs_snippets/deploying/kubernetes/k8s_config_tag_op.py" startAfter="start_k8s_config" endBefore="end_k8s_config" />

Other executors will ignore the `dagster-k8s/config` tag when it is set on an op or asset.

### Precedence rules

Kubernetes configuration can be applied at several different scopes:

- At the deployment level, applying to every run in the deployment
- At the code location, applying to every run launched from the code location
- At the job level, applying to every run launched for that job
- At the step level, if using the <PyObject section="libraries" module="dagster_k8s" object="k8s_job_executor" />

By default, if Kubernetes configuration is specified in multiple places, the configuration is merged recursively. Scalar values will be replaced by the configuration for the more specific scope, dictionary fields will be combined, and list fields will be appended to each other, discarding duplicate values. List fields that cannot be meaningfully appended, like `command` or `args`, are replaced.

Consider the following example:

- **In the Helm chart**, `k8sRunLauncher.runK8sConfig.podSpecConfig` is set to:

  ```json
  {
    "node_selector": { "disktype": "ssd" },
    "dns_policy": "ClusterFirst",
    "image_pull_secrets": [{ "name": "my-secret" }]
  }
  ```

- **But a specific job** has the `dagster-k8s/config` tag set to:

  ```json
  {
    "pod_spec_config": {
      "node_selector": { "region": "east" },
      "dns_policy": "Default",
      "image_pull_secrets": [{ "name": "another-secret" }]
    }
  }
  ```

The job will merge the two `node_selector` dictionaries, append the two `image_pull_secrets` lists, and replace the `dns_policy` scalar value. The resulting `pod_spec_config` will be:

```json
{
  "node_selector": { "disktype": "ssd", "region": "east" },
  "dns_policy": "Default",
  "image_pull_secrets": [{ "name": "my-secret" }, { "name": "another-secret" }]
}
```

To customize this behavior, you can also set the `merge_behavior` key in the `dagster-k8s/config` tag to `SHALLOW` instead of `DEEP`. When `merge_behavior` is set to `SHALLOW`, the dictionaries will be shallowly merged. The configuration for the more specific scope takes precedence if the same key is set in both dictionaries or if scalar values need to be replaced - for example, configuration at the code location level will replace configuration at the deployment level.

To modify the previous example:

- **In the Helm chart**, `k8sRunLauncher.runK8sConfig.podSpecConfig` is set to:

  ```json
  {
    "node_selector": { "disktype": "ssd" },
    "dns_policy": "ClusterFirst",
    "image_pull_secrets": [{ "name": "my-secret" }]
  }
  ```

- **But a specific job** has the `dagster-k8s/config` tag set to:

  ```json
  {
    "pod_spec_config": {
      "node_selector": { "region": "east" },
      "image_pull_secrets": [{ "name": "another-secret" }]
    },
    "merge_behavior": "SHALLOW"
  }
  ```

Since the `merge_behavior` is set to `SHALLOW`, the `node_selector` and `image_pull_secrets` from the job and the DNS policy from the Helm chart will be applied, since only the `node_selector` and `image_pull_secrets` are overridden in the job.

The resulting `pod_spec_config` will be:

```json
{
  "node_selector": { "region": "east" },
  "dns_policy": "ClusterFirst",
  "image_pull_secrets": [{ "name": "another-secret" }]
}
```

:::note

In Dagster code before version 1.7.0, the default merge behavior was `SHALLOW` instead of `DEEP`.

:::

## Configuring an external database

In a real deployment, users will likely want to set up an external PostgreSQL database and configure the `postgresql` section of `values.yaml`.

```yaml
postgresql:
  enabled: false
  postgresqlHost: "postgresqlHost"
  postgresqlUsername: "postgresqlUsername"
  postgresqlPassword: "postgresqlPassword"
  postgresqlDatabase: "postgresqlDatabase"
  service:
    port: 5432
```

Supplying `.Values.postgresql.postgresqlPassword` will create a Kubernetes Secret with key `postgresql-password`, containing the encoded password. This secret is used to supply the Dagster infrastructure with an environment variable that's used when creating the storages for the Dagster instance.

If you use a secrets manager like [Vault](https://www.hashicorp.com/products/vault/kubernetes), it may be convenient to manage this Secret outside of the Dagster Helm chart. In this case, the generation of this Secret within the chart should be disabled, and `.Values.global.postgresqlSecretName` should be set to the name of the externally managed Secret.

```yaml
global:
  postgresqlSecretName: "dagster-postgresql-secret"

generatePostgresqlPasswordSecret: false
```

## Security

Users will likely want to permission a ServiceAccount bound to a properly scoped Role to launch Jobs and create other Kubernetes resources.

Users will likely want to use [Secrets](https://kubernetes.io/docs/concepts/configuration/secret/) for managing secure information such as database logins.

### Separately deploying Dagster infrastructure and user code

It may be desirable to manage two Helm releases for your Dagster deployment: one release for the Dagster infrastructure, which consists of the Dagster webserver and the Dagster daemon, and another release for your User Code, which contains the definitions of your pipelines written in Dagster. This way, changes to User Code can be decoupled from upgrades to core Dagster infrastructure.

To do this, we offer the [`dagster` chart](https://artifacthub.io/packages/helm/dagster/dagster) and the [`dagster-user-deployments` chart](https://artifacthub.io/packages/helm/dagster/dagster-user-deployments).

```shell
$ helm search repo dagster
NAME                            	CHART VERSION	APP VERSION	DESCRIPTION
dagster/dagster                 	0.11.0       	0.11.0     	Dagster is a system for building modern data ap...
dagster/dagster-user-deployments	0.11.0       	0.11.0     	A Helm subchart to deploy Dagster User Code dep...
```

To manage these separate deployments, we first need to isolate Dagster infrastructure to its own deployment. This can be done by disabling the subchart that deploys the User Code in the `dagster` chart. This will prevent the `dagster` chart from creating the services and deployments related to User Code, as these will be managed in a separate release.

```yaml
dagster-user-deployments:
  enableSubchart: false
```

Next, the workspace for the webserver must be configured with the future hosts and ports of the services exposing access to the User Code.

```yaml
dagsterWebserver:
  workspace:
    enabled: true
    servers:
      - host: "k8s-example-user-code-1"
        port: 3030
      - ...
```

Finally, the `dagster-user-deployments` subchart can now be managed in its own release. The list of possible overrides for the subchart can be found in [its `values.yaml`](https://github.com/dagster-io/dagster/blob/master/helm/dagster/charts/dagster-user-deployments/values.yaml).

```shell
helm upgrade --install user-code dagster/dagster-user-deployments -f /path/to/values.yaml
```

## Kubernetes Job and Pod TTL management

If you use a Kubernetes distribution that supports the [TTL Controller](https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/#ttl-controller), then `Completed` and `Failed` [Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/) (and their associated [Pods](https://kubernetes.io/docs/concepts/workloads/pods/)) will be deleted after 1 day. The TTL value can be modified in your job tags:

<CodeExample path="docs_snippets/docs_snippets/deploying/kubernetes/ttl_config_job.py" startAfter="start_ttl" endBefore="end_ttl" />

If you do not use a Kubernetes distribution that supports the [TTL Controller](https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/#ttl-controller), then you can run the following commands:

- Delete Dagster [Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/) older than one day:

  ```shell
  kubectl get job | grep -e dagster-run -e dagster-step | awk 'match($4,/[0-9]+d/) {print $1}' | xargs kubectl delete job
  ```

- Delete completed [Pods](https://kubernetes.io/docs/concepts/workloads/pods/) older than one day:

  ```shell
  kubectl get pod | grep -e dagster-run -e dagster-step | awk 'match($3,/Completed/) {print $0}' | awk 'match($5,/[0-9]+d/) {print $1}' | xargs kubectl delete pod
  ```
