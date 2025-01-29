---
title: Kubernetes agent configuration
sidebar_position: 200
---

:::note
This guide is applicable to Dagster+.
:::

This reference describes the various configuration options Dagster+ currently supports for [Kubernetes agents](setup).

## Viewing the Helm chart

To see the different customizations that can be applied to the Kubernetes agent, you can view the chart's default values:

```shell
helm repo add dagster-plus https://dagster-io.github.io/helm-user-cloud
helm repo update
helm show values dagster-plus/dagster-plus-agent
```

You can also view the chart values on [ArtifactHub](https://artifacthub.io/packages/helm/dagster-cloud/dagster-cloud-agent?modal=values).

## Per-deployment configuration

The [`workspace`](https://artifacthub.io/packages/helm/dagster-cloud/dagster-cloud-agent?modal=values) value of the Helm chart provides the ability to add configuration for all jobs that are spun up by the agent, across all repositories. To add secrets or mounted volumes to all Kubernetes Pods, you can specify your desired configuration under this value.

Additionally, the [`imagePullSecrets`](https://artifacthub.io/packages/helm/dagster-cloud/dagster-cloud-agent?modal=values) value allows you to specify a list of secrets that should be included when pulling the images for your containers.

## Per-location configuration

When [adding a code location](/dagster-plus/deployment/code-locations/) to Dagster+ with a Kubernetes agent, you can use the `container_context` key on the location configuration to add additional Kubernetes-specific configuration. If you're using the Dagster+ Github action, the `container_context` key can also be set for each location in your `dagster_cloud.yaml` file, using the same format.

The following example [`dagster_cloud.yaml`](/dagster-plus/deployment/code-locations/dagster-cloud-yaml) file illustrates the available fields:

```yaml
# dagster_cloud.yaml

locations:
  - location_name: cloud-examples
    image: dagster/dagster-cloud-examples:latest
    code_source:
      package_name: dagster_cloud_examples
    container_context:
      k8s:
        env_config_maps:
          - my_config_map
        env_secrets:
          - my_secret
        env_vars:
          - FOO_ENV_VAR=foo_value
          - BAR_ENV_VAR
        image_pull_policy: Always
        image_pull_secrets:
          - name: my_image_pull_secret
        labels:
          my_label_key: my_label_value
        namespace: my_k8s_namespace
        service_account_name: my_service_account_name
        volume_mounts:
          - mount_path: /opt/dagster/test_mount_path/volume_mounted_file.yaml
            name: test-volume
            sub_path: volume_mounted_file.yaml
        volumes:
          - name: test-volume
            config_map:
              name: test-volume-configmap
        server_k8s_config: # Raw kubernetes config for code servers launched by the agent
          pod_spec_config: # Config for the code server pod spec
            node_selector:
              disktype: standard
          pod_template_spec_metadata: # Metadata for the code server pod
            annotations:
              mykey: myvalue
          deployment_metadata: # Metadata for the code server deployment
            annotations:
              mykey: myvalue
          service_metadata: # Metadata for the code server service
            annotations:
              mykey: myvalue
          container_config: # Config for the main dagster container in the code server pod
            resources:
              limits:
                cpu: 100m
                memory: 128Mi
        run_k8s_config: # Raw kubernetes config for runs launched by the agent
          pod_spec_config: # Config for the run's PodSpec
            node_selector:
              disktype: ssd
          container_config: # Config for the main dagster container in the run pod
            resources:
              limits:
                cpu: 500m
                memory: 1024Mi
          pod_template_spec_metadata: # Metadata for the run pod
            annotations:
              mykey: myvalue
          job_spec_config: # Config for the Kubernetes job for the run
            ttl_seconds_after_finished: 7200
          job_metadata: # Metadata for the Kubernetes job for the run
            annotations:
              mykey: myvalue
```

### Environment variables and secrets

Using the `container_context.k8s.env_vars` and `container_context.k8s.env_secrets` properties, you can specify environment variables and secrets for a specific code location. For example:

```yaml
# dagster_cloud.yaml

location:
  - location_name: cloud-examples
    image: dagster/dagster-cloud-examples:latest
    code_source:
      package_name: dagster_cloud_examples
    container_context:
      k8s:
        env_vars:
          - database_name
          - database_username=hooli_testing
        env_secrets:
          - database_password
```

 | Property      | Description                                                                                                                                                                                                                                                                                                                             |
 |---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
 | `env_vars`    | A list of environment variable names to inject into the job, formatted as `KEY` or `KEY=VALUE`. If only `KEY` is specified, the value will be pulled from the current process.                                                                                                                                                          |
 | `env_secrets` | A list of secret names, from which environment variables for a job are drawn using `envFrom`. Refer to the [Kubernetes documentation](https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables) for more info. |

Refer to the following guides for more info about environment variables:

- [Dagster+ environment variables and secrets](/dagster-plus/deployment/management/environment-variables/)
- [Using environment variables and secrets in Dagster code](/guides/deploy/using-environment-variables-and-secrets)

## Op isolation

By default, each Dagster job will run in its own Kubernetes pod, with each op running in its own subprocess within the pod.

You can also configure your Dagster job with the [`k8s_job_executor`](https://docs.dagster.io/\_apidocs/libraries/dagster-k8s#dagster_k8s.k8s_job_executor) to run each op in its own Kubernetes pod. For example:

```python
from dagster import job
from dagster_k8s import k8s_job_executor

@job(executor_def=k8s_job_executor)
def k8s_job():
    ...
```

## Per-job and per-op configuration

{/* To add configuration to specific Dagster jobs, ops, or assets, use the `dagster-k8s/config` tag. For example, to specify that a job should have certain resource limits when it runs. Refer to [Customizing your Kubernetes deployment for Dagster Open Source](/deployment/guides/kubernetes/customizing-your-deployment#per-job-kubernetes-configuration) for more info. */}
To add configuration to specific Dagster jobs, ops, or assets, use the `dagster-k8s/config` tag. For example, to specify that a job should have certain resource limits when it runs. Refer to [Customizing your Kubernetes deployment for Dagster Open Source](/guides/deploy/deployment-options/kubernetes/customizing-your-deployment) for more info.

## Running as a non-root user

Starting in 0.14.0, the provided `docker.io/dagster/dagster-cloud-agent` image offers a non-root user with id `1001`. To run the agent with this user, you can specify the [`dagsterCloudAgent`](https://artifacthub.io/packages/helm/dagster-cloud/dagster-cloud-agent?modal=values) value in the Helm chart to be:

```yaml
dagsterCloudAgent:
  podSecurityContext:
    runAsUser: 1001
```

We plan to make this user the default in a future release.

## Grant AWS permissions

You can provide your Dagster pods with [permissions to assume an AWS IAM role](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html) using a [Service Account](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/). For example, you might do this to [configure an S3 IO Manager](/guides/deploy/deployment-options/aws#using-s3-for-io-management).

1. [Create an IAM OIDC provider for your EKS cluster](https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html)
2. [Create an IAM role and and attach IAM policies](https://docs.aws.amazon.com/eks/latest/userguide/associate-service-account-role.html)
3. Update the [ Helm chart](#viewing-the-helm-chart) to associate the IAM role with a service account:

   ```bash
    serviceAccount:
    create: true
    annotations:
      eks.amazonaws.com/role-arn: "arn:aws:iam::1234567890:role/my_service_account_role"
   ```

This will allow your agent and the pods it creates to assume the `my_service_account_role` IAM role.
