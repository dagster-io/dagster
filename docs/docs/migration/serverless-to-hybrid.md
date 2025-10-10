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

## 1. Deactivate your Serverless agent

1. In the Dagster+ UI, navigate to the **Deployment > Agents** page.
2. On the right side of the page, click the dropdown arrow and select **Switch to Hybrid**.

![Switch agent to Hybrid dropdown arrow](/images/dagster-plus/deployment/switch-agent-to-hybrid.png)

It may take a few minutes for the agent to deactivate and be removed from the list of agents.

## 2. Create a Hybrid agent

Next, you'll need to create a Hybrid agent to execute your code. Follow the setup instructions for the agent of your choice:

- **[Amazon Web Services (AWS)](/deployment/dagster-plus/hybrid/amazon-ecs)**, which launches user code as Amazon Elastic Container Service (ECS) tasks.
- **[Docker](/deployment/dagster-plus/hybrid/docker)**, which launches user code in Docker containers on your machine.
- **[Microsoft Azure](/deployment/dagster-plus/hybrid/azure)**, which launches user code to Azure infrastructure.
- **[Kubernetes](/deployment/dagster-plus/hybrid/kubernetes)**, which launches user code on a Kubernetes cluster.
- **[Local](/deployment/dagster-plus/hybrid/local)**, which launches user code in operating system subprocesses on your machine.

## 3. Update your code locations' configuration in `dagster_cloud.yaml`

See the documentation for the agent of your choice:

- [Amazon Web Services (AWS)](/deployment/dagster-plus/hybrid/amazon-ecs/configuration-reference#per-location-configuration)
- [Docker](/deployment/dagster-plus/hybrid/docker/configuration)
- [Microsoft Azure](/deployment/dagster-plus/hybrid/azure/acr-user-code#update-the-dagster_cloudyaml-build-configuration-to-use-the-azure-container-registry)
- [Kubernetes](/deployment/dagster-plus/hybrid/kubernetes/configuration#per-location-configuration)

## 4. Confirm successful setup

Once you've set up a Hybrid agent, navigate to the **Deployment > Agents** page in the UI. The new agent should display in the list with a `RUNNING` status:

![Running Hybrid agent displayed in Dagster+ UI](/images/dagster-plus/deployment/running-agent.png)

## 5. Update your build process

Update your build process to publish a new container image and configuration for each code location. To use Dagster's CI/CD process, see the [CI/CD in Dagster+ Hybrid guide](/deployment/dagster-plus/ci-cd/production-deployments/ci-cd-in-hybrid).

## 6. Replace Serverless-only features with their Hybrid equivalents

| Serverless-only feature                                                                                                                                          | Hybrid equivalent                                                                                                                                                                                                                                                                                                         |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Disabling PEX-based deploys](/deployment/dagster-plus/serverless/runtime-environment#disable-pex-deploys) and customizing the Docker image with lifecycle hooks | To customize a code location's runtime environment, you can customize the code location's [Dockerfile](https://github.com/dagster-io/dagster-cloud-hybrid-quickstart/blob/main/Dockerfile) to build its image.                                                                                                            |
| Enabling [non-isolated runs](/deployment/dagster-plus/serverless/run-isolation#non-isolated-runs)                                                                | While this feature doesn't have a direct Hybrid equivalent, you can experiment with the <PyObject section="execution" module="dagster" object="in_process_executor" /> or <PyObject section="execution" module="dagster" object="multiprocess_executor" /> for specific jobs or entire code locations to reduce overhead. |

## Next steps

- Learn about the configuration options for [dagster.yaml](/deployment/oss/dagster-yaml)
