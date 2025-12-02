---
title: Managing branch deployments across multiple deployments
description: Frequent use cases and troubleshooting tips for managing branch deployments when your organization has multiple Dagster+ deployments or environments.
sidebar_position: 7350
tags: [dagster-plus-feature]
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

This guide covers frequent use cases and troubleshooting tips for managing branch deployments when your organization has multiple Dagster+ deployments or environments.

<DagsterPlus />

## Relevant configuration options

We will be using the following configuration options across agent configuration, code locations, and CI/CD:

<Tabs>
<TabItem value="dagster-yaml" label="dagster.yaml (Docker, local, and ECS agents)">

The `deployment(s)`, `branch_deployments`, and `agent_queues` configuration settings are available in the `dagster.yaml` file:

```yaml
# dagster.yaml
dagster_cloud_api:
  # Deployment: a string that identifies the singular full deployment to be served by this agent.
  # This configuration should not be used in conjunction with the 'deployments' configuration option.
  deployment: <deployment name>

  # Deployments: an array of strings that identify the deployments to be served by this agent.
  # This configuration should not be used in conjunction with the 'deployment' configuration option.
  deployments:
    - <Deployment Name>
    - <Optional Additional Deployment Name>

  # Branch deployments: whether this agent will serve branch deployments or not.
  # If enabled, this agent will attempt to serve all branch deployments in the organization and will
  # deploy code locations matching the agent queues that it is serving.
  branch_deployments: <true|false>

agent_queues:
  # If true, this agent will request for code locations that aren't annotated with a specific queue
  include_default_queue: True

  # The additional queues that this agent will serve.
  additional_queues:
    - special-queue
```

For more information about configuring the Docker, local, or ECS agents, see their documentation:

- [Docker agent](/deployment/dagster-plus/hybrid/docker)
- [Local agent](/deployment/dagster-plus/hybrid/local)
- [Amazon ECS agent](/deployment/dagster-plus/hybrid/amazon-ecs)

</TabItem>
<TabItem value="helm" label="Helm chart values (Kubernetes agent)">

The `deployment(s)`, `branchDeployments`, and `agentQueues` configuration settings are available in the Helm chart values file. The values are located under the `dagsterCloud` key:

```yaml
dagsterCloud:
  deployment: <deployment name>
  deployments:
    - <Deployment Name>
    - <Optional Additional Deployment Name>
  branchDeployments: <true|false>
  agentQueues:
    includeDefaultQueue: <true|false>
    additionalQueues:
      - special-queue
```

For more information about the Kubernetes agent setup and Helm chart values, see:

- [Dagster+ Kubernetes agent setup](/deployment/dagster-plus/hybrid/kubernetes/setup)
- [Dagster+ Helm chart values](https://artifacthub.io/packages/helm/dagster-cloud/dagster-cloud-agent?modal=values)

</TabItem>
<TabItem value="build_yaml" label="build.yaml (Optional queue routing configuration for code locations)">

:::note

If you have an older Dagster+ deployment, you may have a `dagster_cloud.yaml` file instead of a `build.yaml` file.

:::

Whether in the context of a [full deployment](/deployment/dagster-plus/deploying-code/full-deployments) or a [branch deployment](/deployment/dagster-plus/deploying-code/branch-deployments), you can configure the code location to be served on a specific agent queue:

```yaml
# build.yaml
locations:
  - location_name: <location name>
    # The named queue that this code location will be served on. If not set, the default queue is used.
    agent_queue: <queue name>
```

For more information about agent queue routing or code location configuration, refer to:

- [Agent queue routing](/deployment/dagster-plus/hybrid/multiple#routing-requests-to-specific-agents)
- [build.yaml code location configuration reference](/deployment/dagster-plus/management/build-yaml)

</TabItem>

</Tabs>

:::info

The [base deployment](/deployment/dagster-plus/deploying-code/branch-deployments/configuring-branch-deployments#changing-the-base-deployment) of a branch deployment does not affect which agents will serve the branch deployment.

:::

## Frequent use cases

### Configuring branch deployments to be served by a single agent

Ensure that one and only one agent is configured to serve branch deployments. See `dagster_cloud_api.branch_deployments` in `dagster.yaml` (for Docker, local, and ECS agents) or `dagsterCloud.branchDeployments` in the Helm chart (for Kubernetes agents).

Given a 'development' and a 'production' deployment, and the intention to only run branch deployments in development, the development deployment's agent(s) should be configured to `branch_deployments = true` and the production deployment agent(s) should be configured to `branch_deployments = false`.

### Configuring a dedicated agent to serve only branch deployments

You can configure an agent that does not serve any deployment but branch deployments by omitting the deployment
option in the agent's configuration.

```yaml
dagster_cloud_api:
  branch_deployments: true
```

### Providing specific configuration values to a given code location on a branch deployment

You can use Dagster+ environment variables to pass the appropriate environment variables with the branch deployment scope. See [Setting environment variables with the Dagster+ UI](/deployment/dagster-plus/management/environment-variables/dagster-ui).
On Hybrid, you can also use [Setting environment variables using agent config](/deployment/dagster-plus/management/environment-variables/agent-config), or leverage the underlying platform features (such as Kubernetes ConfigMaps or Secrets) to pass these values.

See: [Dagster+ branch deployments](/guides/operate/configuration/using-environment-variables-and-secrets#dagster-branch-deployments)

### Setting the concurrency limit for runs across all branch deployments

There is an organization-scoped setting `max_concurrent_branch_deployment_runs` that controls concurrency across all branch deployments. By default its value is 50.

Modifying organization-scoped settings can only be done using the [dagster-cloud CLI](/api/clis/dagster-cloud-cli). The CLI must be [authenticated](/api/clis/dagster-cloud-cli/installing-and-configuring#setting-up-the-configuration-file) with a user token for a user that has the [Organization Admin role](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions#dagster-user-roles).

To view the organization settings in the terminal:

```bash
dagster-cloud organization settings get # max_concurrent_branch_deployment_runs: 50
```

To modify organization settings, first save the settings to a `YAML` file on your local system:

```bash
dagster-cloud organization settings get > org-settings.yaml
```

Edit the contents of this `YAML` file and save it. Then run the below command to sync the changes:

```bash
dagster-cloud organization settings set-from-file org-settings.yaml
```

### Serving specific code location branch deployments on specific agents when you have multiple agents in distinct environments

This requires using the [agent queue routing](/deployment/dagster-plus/hybrid/multiple#routing-requests-to-specific-agents) configuration. Each environment would need its specific queues to route the code location to the right agent.

For example, given two deployments, 'east' and 'west', you could configure those agents respectively with the queues `east-queue` and `west-queue`. Then, for a code location intended to work only in the `east` deployment, you would set the `agent_queue` to `east-queue` in the code location configuration.

See `dagster_cloud_api.agent_queues.additional_queues` in `dagster.yaml` (for Docker, local, and ECS agents) or `dagsterCloud.agentQueues.additionalQueues` in the Helm chart (for Kubernetes agents).

### Ensuring branch deployments are served on the correct agent when you have a Serverless deployment and one or more Hybrid deployments with incompatible code locations

In addition to the previous answer about using multiple agents in distinct environments, since the Serverless agent always serves the default queue only, the Hybrid agent(s) would need to also exclude the default queue.

See `dagster_cloud_api.agent_queues` in `dagster.yaml` (for Docker, local, and ECS agents) or `dagsterCloud.agentQueues` in the Helm chart (for Kubernetes agents) for both the `include_default_queue` / `includeDefaultQueue` and `additional_queues` / `additionalQueues` options.

## Troubleshooting

### Agent failures that prevent branch deployments from being properly served

- Insufficient memory allocation that results in an OOMKill
- Any situation causing frequent rescheduling of the agent pod or task, such as node compression or evictions on Kubernetes.

### No agent is serving my branch deployment

- Ensure that at least one agent is configured to serve branch deployments. See `dagster_cloud_api.branch_deployments` in `dagster.yaml` (for Docker, local, and ECS agents) or `dagsterCloud.branchDeployments` in the Helm chart (for Kubernetes agents).
- This agent's token must also be either organization-scoped or have the "All branch deployments" permission. See [Managing agent tokens](/deployment/dagster-plus/management/tokens/agent-tokens#managing-agent-tokens)

### I have configured my agent to serve branch deployments, but now I have no agent serving my full deployment

- Make sure that at least one agent is configured to serve each of your full deployments. See `dagster_cloud_api.branch_deployments` in `dagster.yaml` (for Docker, local, and ECS agents) or `dagsterCloud.branchDeployments` in the Helm chart (for Kubernetes agents).
