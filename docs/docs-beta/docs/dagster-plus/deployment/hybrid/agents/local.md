---
title: "Running a Dagster+ agent locally"
displayed_sidebar: "dagsterPlus"
sidebar_position: 40
sidebar_label: "Local"
---

You can set up a local agent to execute pipelines launched in Dagster+. Local agents are a good way to experiment with Dagster+ locally before deploying a more scalable hybrid agent like [Kubernetes](dagster-plus/hybrid/agents/kubernetes) or [Amazon ECS](dagster-plus/hybrid/agents/amazon-ecs-new-vpc).

:::warning
Local agents aren't well suited for most production use cases. This is because local agents:
- Don't have the same CI / CD update strategies as the other agents.
- Need a separate process running on the sever hosting the agent to pull in changes to your Dagster project.
- Need to be restarted to deploy changes.
:::

:::note
If you're running the local agent in production, make sure you've set up a supervisor to automatically restart the agent process if it crashes. You'll also want a system in place to alert you if the VM or container dies, or to automatically restart it.
:::

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- **Organization Admin** permissions in your Dagster+ account.
- **To install the `dagster-cloud` CLI** in the same environment where the agent will run. We recommend using a Python virtual environment for your Dagster application code and its dependencies.
    ```bash
    pip install dagster-cloud
    ```

</details>

## Step 1: Generate an agent token

Your local agent will need a token to authenticate with your Dagster+ account. To generate an agent token:
1. Click the **user menu (your icon) -> Organization Settings**.
2. In the **Organization Settings** page, click the **Tokens** tab.
3. Click the **+ Create agent token** button.
4. After the token has been created, click **Reveal token**.
5. Copy the token and keep it somewhere handy. It will be used in Step 2.
6. We recommend giving the agent token a description to distinguish it from other tokens in the future.


## Step 2: Configure the local agent

1. Create a directory to act as your Dagster home. We'll use `~/dagster_home` in the rest of this guide, but the directory can be located wherever you want.
2. In the directory you created, create a `dagster.yaml` file with the following content:
    <CodeExample filePath="dagster-plus/deployment/hybrid/agents/local_dagster.yaml" language="yaml" title="dagster.yaml" />
3. In the file, fill in the following:
    - `agent_token` - Add the agent token you created in Step 1.
    - `deployment` - Enter the deployment name associated with this instance of the agent. In the preceding example, we specified `prod` as the deployment.

4. Save the file.

You can find more configuration options for `dagster.yaml` in the [`dagster.yaml` reference](/todo).

## Step 3: Run the agent

To start the agent, run the following command and pass the path to the `dagster.yaml` file you created in Step 2:
```bash
dagster-cloud agent run ~/dagster_home/
```

To view the agent in Dagster+, click the Dagster icon in the top left to navigate to the **Deployment -> Agents** page. You should see the agent running in the **Agent statuses** section:

SCREENSHOT

## Next steps

- Add a [code location](/todo) to your Dagster+ deployment.
