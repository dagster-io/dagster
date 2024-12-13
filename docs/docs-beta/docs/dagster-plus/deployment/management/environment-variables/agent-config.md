---
title: "Set environment variables using agent config"
sidebar_position: 300
sidebar_label: "Set with agent config"
---

import ThemedImage from '@theme/ThemedImage';

:::note
This guide is applicable to Dagster+
:::

In this guide, we'll walk you through setting environment variables for a Dagster+ [Hybrid deployment](/dagster-plus/deployment/deployment-types/hybrid) using the Hybrid agent's configuration.

There are two ways to set environment variables:

- **On a per-code location basis**, which involves modifying the `dagster_cloud.yaml` file. **Note**: This approach is functionally the same as [setting environment variables using the Dagster+ UI](/dagster-plus/deployment/management/environment-variables/dagster-ui). Values will pass through Dagster+.
- **For a full deployment and all the code locations it contains**. This approach makes variables available for all code locations in a full Dagster+ deployment. As values are pulled from the user cluster, values will bypass Dagster+ entirely.

## Prerequisites

To complete the steps in this guide, you'll need:

- A Dagster+ account using [Hybrid deployment](/dagster-plus/deployment/deployment-types/hybrid/)
- An existing [Hybrid agent](/dagster-plus/deployment/deployment-types/hybrid/#dagster-hybrid-agents)
- **Editor**, **Admin**, or **Organization Admin** permissions in Dagster+

## Setting environment variables for a code location

:::note
  To set environment variables, you need{" "}
  <a href="/dagster-plus/account/managing-users">
    one of the following user roles
  </a>{" "}
  in Dagster+:
  <ul>
    <li>Organization Admin, or</li>
    <li>
      Editor or Admin. <strong>Note:</strong> Editors and Admins can only set
      environment variables in full deployments where you're an Editor or Admin.
    </li>
  </ul>
:::

Setting environment variables for specific code locations is accomplished by adding them to your agent's configuration in your project's [`dagster_cloud.yaml` file](/dagster-plus/deployment/management/settings/). The `container_context` property in this file sets the variables in the agent's environment.

**Note**: This approach is functionally the same as [setting environment variables using the Dagster+ UI](/dagster-plus/deployment/management/environment-variables/dagster-ui).

How `container_context` is configured depends on the agent type. Click the tab for your agent type to view instructions.

<Tabs>
  <TabItem value="Amazon ECS">

### Amazon ECS agents

<!--<AmazonEcsEnvVarsConfiguration />-->

After you've modified `dagster_cloud.yaml`, redeploy the code location in Dagster+ to apply the changes:

<ThemedImage
  alt="Highlighted Redeploy option in the dropdown menu next to a code location in Dagster+"
  style={{width:'100%', height: 'auto'}}
  sources={{
    light: '/images/dagster-cloud/developing-testing/code-locations/redeploy-code-location.png',
    dark: '/images/dagster-cloud/developing-testing/code-locations/redeploy-code-location.png',
  }}
/>


</TabItem>
<TabItem value="Docker">

### Docker agents

<!--<DockerEnvVarsConfiguration />-->

After you've modified `dagster_cloud.yaml`, redeploy the code location in Dagster+ to apply the changes:

<ThemedImage
  alt="Highlighted Redeploy option in the dropdown menu next to a code location in Dagster+"
  style={{width:'100%', height: 'auto'}}
  sources={{
    light: '/images/dagster-cloud/developing-testing/code-locations/redeploy-code-location.png',
    dark: '/images/dagster-cloud/developing-testing/code-locations/redeploy-code-location.png',
  }}
/>

</TabItem>
<TabItem value="Kubernetes">

### Kubernetes agents

<!--<K8sEnvVarsConfiguration />-->

After you've modified `dagster_cloud.yaml`, redeploy the code location in Dagster+ to apply the changes:

<ThemedImage
  alt="Highlighted Redeploy option in the dropdown menu next to a code location in Dagster+"
  style={{width:'100%', height: 'auto'}}
  sources={{
    light: '/images/dagster-cloud/developing-testing/code-locations/redeploy-code-location.png',
    dark: '/images/dagster-cloud/developing-testing/code-locations/redeploy-code-location.png',
  }}
/>

</TabItem>
</Tabs>

## Setting environment variables for full deployments

:::note
  If you're a Dagster+{" "}
  <a href="/dagster-plus/account/managing-users">
    <strong>Editor</strong> or <strong>Admin</strong>
  </a>
  , you can only set environment variables for full deployments where you're an <strong>
    Editor
  </strong> or <strong>Admin</strong>.
:::

Setting environment variables for a full deployment will make the variables available for all code locations in the full deployment. Using this approach will pull variable values from your user cluster, bypassing Dagster+ entirely.

Click the tab for your agent type to view instructions.

<Tabs>
  <TabItem value="Amazon ECS">

### Amazon ECS agents

To make environment variables accessible to a full deployment with an Amazon ECS agent, you'll need to modify the agent's CloudFormation template as follows:

1. Sign in to your AWS account.

2. Navigate to **CloudFormation** and open the stack for the agent.

3. Click **Update**.

4. Click **Edit template in designer**.

5. In the section that displays, click **View in Designer**. The AWS template designer will display.

6. In the section displaying the template YAML, locate the `AgentTaskDefinition` section:

    <ThemedImage
      alt="Highlighted AgentTaskDefinition section of the AWS ECS agent CloudFormation template in the AWS Console"
      style={{width:'100%', height: 'auto'}}
      sources={{
        light: '/images/dagster-cloud/developing-testing/environment-variables/aws-ecs-cloudformation-template.png',
        dark: '/images/dagster-cloud/developing-testing/environment-variables/aws-ecs-cloudformation-template.png',
      }}
    />


7. In the `user_code_launcher.config` portion of the `AgentTaskDefinition` section, add the environment variables as follows:

   ```yaml
   user_code_launcher:
     module: dagster_cloud.workspace.ecs
     class: EcsUserCodeLauncher
     config:
       cluster: ${ConfigCluster}
       subnets: [${ConfigSubnet}]
       service_discovery_namespace_id: ${ServiceDiscoveryNamespace}
       execution_role_arn: ${TaskExecutionRole.Arn}
       task_role_arn: ${AgentRole}
       log_group: ${AgentLogGroup}
       env_vars:
         - SNOWFLAKE_USERNAME=dev
         - SNOWFLAKE_PASSWORD       ## pulled from agent environment
   ' > $DAGSTER_HOME/dagster.yaml && cat $DAGSTER_HOME/dagster.yaml && dagster-cloud agent run"
   ```

8. When finished, click the **Create Stack** button:

    <ThemedImage
      alt="Highlighted Create Stack button in the AWS Console"
      style={{width:'100%', height: 'auto'}}
      sources={{
        light: '/images/dagster-cloud/developing-testing/environment-variables/aws-ecs-save-template.png',
        dark: '/images/dagster-cloud/developing-testing/environment-variables/aws-ecs-save-template.png',
      }}
    />


9. You'll be redirected back to the **Update stack** wizard, where the new template will be populated. Click **Next**.

10. Continue to click **Next** until you reach the **Review** page.

11. Click **Submit** to update the stack.

</TabItem>
<TabItem value="Docker">

### Docker agents

To make environment variables accessible to a full deployment with a Docker agent, you'll need to modify your project's `dagster.yaml` file.

In the `user_code_launcher` section, add an `env_vars` property as follows:

```yaml
# dagster.yaml

user_code_launcher:
  module: dagster_cloud.workspace.docker
  class: DockerUserCodeLauncher
  config:
    networks:
      - dagster_cloud_agent
    env_vars:
      - SNOWFLAKE_PASSWORD # value pulled from agent's environment
      - SNOWFLAKE_USERNAME=dev
```

In `env_vars`, specify the environment variables as keys (`SNOWFLAKE_PASSWORD`) or key-value pairs (`SNOWFLAKE_USERNAME=dev`). If only `KEY` is provided, the value will be pulled from the agent's environment.

</TabItem>
<TabItem value="Kubernetes">

### Kubernetes agents

To make environment variables available to a full deployment to a full deployment with a Kubernetes agent, you'll need to modify and upgrade the Helm chart's `values.yaml`.

1. In `values.yaml`, add or locate the `workspace` value.

2. Add an `envVars` property as follows:

   ```yaml
   # values.yaml

   workspace:
     envVars:
       - SNOWFLAKE_PASSWORD # value pulled from agent's environment
       - SNOWFLAKE_USERNAME=dev
   ```

3. In `envVars`, specify the environment variables as keys (`SNOWFLAKE_PASSWORD`) or key-value pairs (`SNOWFLAKE_USERNAME=dev`). If only `KEY` is provided, the value will be pulled from the local (agent's) environment.

4. Upgrade the Helm chart.

</TabItem>
</Tabs>
