---
title: 'Managing branch deployments across multiple deployments'
sidebar_position: 500
---

# Managing branch deployments across multiple deployments

:::note
This guide applies to Dagster+.
:::

This section will present a few tips and pitfalls for managing branch deployments when your organization has multiple deployments or environments.

## Review of configuration options relevant to this section.

We will be leveraging the following configuration options across agent, code locations and CI/CD. Reviewing them first is a great start.

### dagster.yaml (for docker, local and ECS agent)

The `deployment(s)`, `branch_deployment`, and `agent_queues` configuration settings are available in the `dagster.yaml`.

```yaml
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

For more information about configuring the docker, local or ECS agent, refer to their respective documentation:

- [Docker agent](/dagster-plus/deployment/deployment-types/hybrid/docker/)
- [Local agent](/dagster-plus/deployment/deployment-types/hybrid/local/)
- [Amazon ECS agent](/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs/)

### Helm chart values (for the Kubernetes agent)

The same values are available in the Helm chart values file, albeit with slightly different names. The values are
located under the `dagsterCloud` key.

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

For more information about the Helm chart and its values, refer to:

- [Dagster+ Kubernetes agent setup](/dagster-plus/deployment/deployment-types/hybrid/kubernetes/setup)
- [Dagster+ Helm chart values](https://artifacthub.io/packages/helm/dagster-cloud/dagster-cloud-agent?modal=values)

### Code location optional queue routing configuration (dagster_cloud.yaml)

Whether in the context of a full deployment or a branch deployment, you can configure the code location to be served on a specific agent queue.

```yaml
locations:
  - location_name: <location name>
    # The named queue that this code location will be served on. If not set, the default queue is used.
    agent_queue: <queue name>
```

For more information about agent queue routing or code location configuration, refer to:

- [Code location configuration reference](/dagster-plus/deployment/code-locations/dagster-cloud-yaml)
- [Agent queue routing](/dagster-plus/deployment/deployment-types/hybrid/multiple#routing-requests-to-specific-agents)

### A note about base deployment in CI/CD

In the context of CI/CD, you can explicitly set a base deployment for your branch deployments.

The effect of the base deployment has two main purposes:

- It sets which full deployment is used to propagate Dagster+ managed environment variables that are scoped for branch deployments.
- It is used in the UI to track changes to the branch deployment from its parent full deployment.

:::note
The base deployment of a branch deployment does not impact which agents will serve the branch deployment.
:::

## Frequent use cases

### How to configure my branch deployments to be served by a single agent?

Ensure that one and only one agent is configured to serve branch deployments. See `dagster_cloud_api.branch_deployments` (or `dagsterCloud.branchDeployments` for Helm users).

Given a 'development' and a 'production' deployment and the intention to only run branch deployments in development, the first's agent(s) should be configured to `branch_deployments = true` and the second to `branch_deployments = false`.

### I have multiple agents in distinct environments. How can I get specific code location branch deployments to be served on specific agents?

This requires using the [agent queue routing](/dagster-plus/deployment/deployment-types/hybrid/multiple#routing-requests-to-specific-agents) configuration. Each environment would need its specific queues to route the code location to the right agent.

For example, given two deployments 'east' and 'west' you could configure those agents respectively with the queues `east-queue` and `west-queue`. Then, for a code location intended to work only in the `east` deployment, you would set the `agent_queue` to `east-queue` in the code location configuration.

See `dagster_cloud_api.agent_queues.additional_queues` (or `dagsterCloud.agentQueues.additionalQueues` in the Helm chart's values).

### I have a serverless deployment and one or many hybrid deployments. Code locations are not compatible across these deployments. How can I ensure that my branch deployments are served on the correct agent?

In addition to the previous answer about using multiple agents in distinct environments, since the serverless agent always serves the default queue only, the hybrid agent(s) would need to also exclude the default queue.

See `dagster_cloud_api.agent_queues` (or `dagsterCloud.agentQueues` for Helm users) for both the `include_default_queue` and `additional_queues` options.

### How can I provide specific configuration values to a given code location on a branch deployment?

You can use Dagster+ environment variables to pass the appropriate environment variables with the branch deployment scope. See [Setting environment variables with the Dagster+ UI](/dagster-plus/deployment/management/environment-variables/dagster-ui).
On Hybrid, you can also use [Setting environment variables using agent config](/dagster-plus/deployment/management/environment-variables/agent-config), or leverage the underlying platform features (such as Kubernetes ConfigMaps or Secrets) to pass these values.

See: [Dagster+ branch deployments](/guides/deploy/using-environment-variables-and-secrets#dagster-branch-deployments)

### Can I have a dedicated agent serving only branch deployments?

Yes, you can configure an agent that does not serve any deployment but branch deployments by omitting the deployment
option in the agent's configuration.

```yaml
dagster_cloud_api:
  branch_deployments: true
```

## Pitfalls and misconfigurations

### No agent is serving my branch deployment

- You need to ensure that at least one agent is configured to serve branch deployments. See `dagster_cloud_api.branch_deployments` (or `dagsterCloud.branchDeployments` for Helm users).
- This agent's token must also be either organization-scoped or have the "All branch deployments" permission. See [Managing agent tokens](/dagster-plus/deployment/management/tokens/agent-tokens#managing-agent-tokens)

### I have configured my agent to serve branch deployments, but now I have no agent serving my full deployment

- Make sure that at least one agent is configured to serve each of your full deployments. See `dagster_cloud_api.deployment(s)` (or `dagsterCloud.deployment(s)` for Helm users).

### Agent failures that prevent branch deployments from being properly served

- Insufficient memory allocation that results in an OOMKill
- Any situation causing frequent rescheduling of the agent pod or task, such as node compression or evictions on Kubernetes.
