---
description: Migrate from Dagster+ Serverless to Hybrid deployment to leverage your own infrastructure to execute your code.
sidebar_label: Dagster+ Serverless to Hybrid
sidebar_position: 40
title: Migrate from Dagster+ Serverless to Hybrid
---

After using a [Dagster+ Serverless](/deployment/dagster-plus/serverless) deployment, you may decide to use your own infrastructure to execute your code. Transitioning to a [Hybrid deployment](/deployment/dagster-plus/hybrid) only requires a few steps, and can be done without any loss of execution history or metadata, allowing you to maintain continuity and control over your operations.

:::warning

Transitioning from Serverless to Hybrid requires some downtime, as your Dagster+ deployment will temporarily not have an agent to execute user code.

:::

## Prerequisites

To follow the steps in this guide, you'll need [**Organization Admin** permissions](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions) in your Dagster+ account.

## Step 1: Deactivate your Serverless agent

1. In the Dagster+ UI, navigate to the **Deployment > Agents** page.
2. On the right side of the page, click the dropdown arrow and select **Switch to Hybrid**.

![Switch agent to Hybrid dropdown arrow](/images/dagster-plus/deployment/switch-agent-to-hybrid.png)

It may take a few minutes for the agent to deactivate and be removed from the list of agents.

## Step 2: Create a Hybrid agent

Next, you'll need to create a Hybrid agent to execute your code. Follow the setup instructions for the agent of your choice:

- **[Amazon Web Services (AWS)](/deployment/dagster-plus/hybrid/amazon-ecs)**, which launches user code as Amazon Elastic Container Service (ECS) tasks.
- **[Docker](/deployment/dagster-plus/hybrid/docker)**, which launches user code in Docker containers on your machine.
- **[Microsoft Azure](/deployment/dagster-plus/hybrid/azure)**, which launches user code to Azure infrastructure.
- **[Kubernetes](/deployment/dagster-plus/hybrid/kubernetes)**, which launches user code on a Kubernetes cluster.
- **[Local](/deployment/dagster-plus/hybrid/local)**, which launches user code in operating system subprocesses on your machine.

## Step 3: Update your code locations' configuration in `build.yaml`

See the documentation for the agent of your choice:

- [Amazon Web Services (AWS)](/deployment/dagster-plus/hybrid/amazon-ecs/configuration-reference#per-location-configuration)
- [Docker](/deployment/dagster-plus/hybrid/docker/configuration)
- [Microsoft Azure](/deployment/dagster-plus/hybrid/azure/acr-user-code#step-34-update-the-buildyaml-build-configuration-to-use-the-azure-container-registry)
- [Kubernetes](/deployment/dagster-plus/hybrid/kubernetes/configuration#per-location-configuration)

:::note

If you have an older Dagster+ deployment, you may have a `dagster_cloud.yaml` file instead of a `build.yaml` file.

:::

## Step 4: Confirm successful setup

Once you've set up a Hybrid agent, navigate to the **Deployment > Agents** page in the UI. The new agent should display in the list with a `RUNNING` status:

![Running Hybrid agent displayed in Dagster+ UI](/images/dagster-plus/deployment/running-agent.png)

## Step 5: Update your build process

Update your build process to publish a new container image and configuration for each code location. To use Dagster's CI/CD process, see [Configuring CI/CD in Dagster+](/deployment/dagster-plus/deploying-code/configuring-ci-cd).

## Step 6: Replace Serverless-only features with their Hybrid equivalents

| Serverless-only feature                                                                                                                                          | Hybrid equivalent                                                                                                                                                                                                                                                                                                         |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Disabling PEX-based deploys](/deployment/dagster-plus/serverless/runtime-environment#disable-pex-deploys) and customizing the Docker image with lifecycle hooks | To customize a code location's runtime environment, you can customize the code location's [Dockerfile](https://github.com/dagster-io/dagster-cloud-hybrid-quickstart/blob/main/Dockerfile) to build its image.                                                                                                            |
| Enabling [non-isolated runs](/deployment/dagster-plus/serverless/run-isolation#non-isolated-runs)                                                                | While this feature doesn't have a direct Hybrid equivalent, you can experiment with the <PyObject section="execution" module="dagster" object="in_process_executor" /> or <PyObject section="execution" module="dagster" object="multiprocess_executor" /> for specific jobs or entire code locations to reduce overhead. |

## 7. Migrate asset data to your own storage (optional)

In Serverless deployments, asset values are stored by default using Dagster-managed S3 storage. After switching to Hybrid, you may want to migrate that data to your own S3 bucket or other storage backend so that your assets remain loadable under the new IO manager configuration. The alternative is to re-materialize all assets against your new storage backend, but this may be time-consuming for large assets or asset graphs.

You can use <PyObject section="io-managers" module="dagster" object="migrate_io_storage" /> to copy all materialized asset data from the Serverless-managed IO manager to your new IO manager without re-materializing any assets.

The example below shows a job that migrates asset data from the default IO manager (which in Serverless is Dagster-managed S3 storage) to a new S3 bucket that you control:

<CodeExample
  path="docs_snippets/docs_snippets/guides/migrations/migrate_io_storage.py"
  language="python"
  startAfter="start_migrate_io_storage"
  endBefore="end_migrate_io_storage"
/>

:::note

- The `context` argument provides both the set of assets to migrate and the
  source IO manager for each asset— they are resolved from the code location
  that the currently executing op belongs to. Alternatively, you can pass a
  `definitions` argument (along with an `instance`) instead of `context` to
  provide the assets and IO managers explicitly. In a standard serverless
  deployment, all assets will by default use the same Dagster-managed S3 IO
  manager, but in other deployments there may be multiple IO managers in use.
  The `destination_io_manager` is the same for all assets and should be an
  instance of the new IO manager you want to write data to.
- Progress is logged to the Dagster event log when `migrate_io_storage` is called inside an op.
- For large partitioned assets, use `batch_partitions=True` to migrate partitions in batches using `PartitionKeyRange` contexts instead of one at a time.
- Use the `transform` parameter if the in-memory Python type differs between your source and destination IO managers. For example, if your source IO manager deserializes data to Pandas DataFrames but your destination IO manager serializes PyArrow tables, you could provide a transform function that converts the DataFrame to a PyArrow table in memory before writing it to the new storage backend.

:::

## Next steps

- Learn about the configuration options for [dagster.yaml](/deployment/oss/dagster-yaml)
