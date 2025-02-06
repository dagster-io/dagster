---
title: Docker agent setup
sidebar_position: 100
---

:::note
This guide is applicable to Dagster+.
:::

In this guide, you'll configure and run a Docker agent. Docker agents are used to launch your code in Docker containers.

## Prerequisites

To complete the steps in this guide, you'll need:

- **Permissions in Dagster+ that allow you to manage agent tokens**. Refer to the [User permissions documentation](/dagster-plus/features/authentication-and-access-control/rbac/user-roles-permissions/) for more info.
- **To have Docker installed**
- **Access to a container registry to which you can push images with Dagster code.** Additionally, your Docker agent must have the permissions required to pull images from the registry.

  This can be:

  - A self-hosted registry,
  - A public registry such as [DockerHub](https://hub.docker.com/), or
  - A managed offering such as [Amazon ECR](https://aws.amazon.com/ecr/), [Azure CR](https://azure.microsoft.com/en-us/services/container-registry/#overview), or [Google CR](https://cloud.google.com/container-registry)

## Step 1: Generate a Dagster+ agent token

In this step, you'll generate a token for the Dagster+ agent. The Dagster+ agent will use this to authenticate to the agent API.

1. Sign in to your Dagster+ instance.
2. Click the **user menu (your icon) > Organization Settings**.
3. In the **Organization Settings** page, click the **Tokens** tab.
4. Click the **+ Create agent token** button.
5. After the token has been created, click **Reveal token**.

Keep the token somewhere handy - you'll need it to complete the setup.

## Step 2: Create a Docker agent

1. Create a Docker network for your agent:

   ```shell
   docker network create dagster_cloud_agent
   ```

2. Create a `dagster.yaml` file:

   ```yaml
   instance_class:
     module: dagster_cloud.instance
     class: DagsterCloudAgentInstance

   dagster_cloud_api:
     agent_token: <YOUR_AGENT_TOKEN>
     branch_deployments: true # enables branch deployments
     deployment: prod

   user_code_launcher:
     module: dagster_cloud.workspace.docker
     class: DockerUserCodeLauncher
     config:
       networks:
         - dagster_cloud_agent
   ```

3. In the file, fill in the following:

   - `agent_token` - Add the agent token you created in [Step 1](#step-1-generate-a-dagster-agent-token)
   - `deployment` - Enter the deployment associated with this instance of the agent.

     In the above example, we specified `prod` as the deployment. This is present when Dagster+ organizations are first created.

4. Save the file.

## Step 3: Start the agent

Next, you'll start the agent as a container. Run the following command in the same folder as your `dagster.yaml` file:

```shell
docker run \
  --network=dagster_cloud_agent \
  --volume $PWD/dagster.yaml:/opt/dagster/app/dagster.yaml:ro \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  -it docker.io/dagster/dagster-cloud-agent:latest \
  dagster-cloud agent run /opt/dagster/app
```

This command:

- Starts the agent with your local `dagster.yaml` mounted as a volume
- Starts the system Docker socket mounted as a volume, allowing the agent to launch containers.

To view the agent in Dagster+, click the Dagster icon in the top left to navigate to the **Status** page and click the **Agents** tab. You should see the agent running in the **Agent statuses** section:

![Instance Status](/images/dagster-plus/deployment/agents/dagster-cloud-instance-status.png)

## Credential Helpers

If your images are stored in a private registry, configuring a [Docker credentials helper](https://docs.docker.com/engine/reference/commandline/login/#credential-helpers) allows the agent to log in to your registry. The agent image comes with several popular credentials helpers preinstalled:

- [docker-credential-ecr-login](https://github.com/awslabs/amazon-ecr-credential-helper)
- [docker-credential-gcr](https://github.com/GoogleCloudPlatform/docker-credential-gcr)

These credential helpers generally are configured in `~/.docker.config.json`. To use one, make sure you mount that file as a volume when you start your agent:

```shell
  docker run \
    --network=dagster_cloud_agent \
    --volume $PWD/dagster.yaml:/opt/dagster/app/dagster.yaml:ro \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    --volume ~/.docker/config.json:/root/.docker/config.json:ro \
    -it docker.io/dagster/dagster-cloud-agent:latest \
    dagster-cloud agent run /opt/dagster/app
```

## Next steps

Now that you've got your agent running, what's next?

- **If you're getting Dagster+ set up**, the next step is to [add a code location](/dagster-plus/deployment/code-locations/) using the agent.
- **If you're ready to load your Dagster code**, refer to the [Adding Code to Dagster+](/dagster-plus/deployment/code-locations/) guide for more info.
