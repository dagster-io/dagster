---
title: "Running a Dagster+ agent locally"
displayed_sidebar: "dagsterPlus"
sidebar_position: 40
sidebar_label: "Local"
---

Local agents are a good way to experiment with Dagster+ before deploying a more scalable Hybrid agent like [Kubernetes](/dagster-plus/deployment/hybrid/agents/kubernetes) or [Amazon ECS](/todo).

:::note
Local agents aren't well suited for most production use cases. If you're running the local agent in production, make sure that:

- You've set up a supervisor to automatically restart the agent process if it crashes
- You're alerted if the VM or container dies, or to automatically restart it
:::

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- **Organization Admin** permissions in your Dagster+ account
- **To install the `dagster-cloud` CLI** in the same environment where the agent will run. We recommend using a Python virtual environment for your Dagster application code and its dependencies.

    ```bash
    pip install dagster-cloud
    ```
</details>

## Step 1: Generate an agent token

Your local agent will need a token to authenticate with your Dagster+ account. To generate an agent token:

1. Click the **user menu (your icon) > Organization Settings**.
2. In the **Organization Settings** page, click the **Tokens** tab.
3. Click the **+ Create agent token** button.
4. After the token has been created, click **Reveal token**.
5. Save this token as an environment variable on the machine where the local agent will run. You can choose any name for this environment variable, but `$DAGSTER_AGENT_TOKEN` will be used in the rest of this guide.
6. Give the agent token a description to distinguish it from other tokens in the future.

## Step 2: Configure the local agent

1. Create a directory to act as your Dagster home. This guide uses `~/dagster_home`, but the directory can be located wherever you want.
2. In the new directory, create a `dagster.yaml` file with the following:
    <CodeExample filePath="dagster-plus/deployment/hybrid/agents/local_dagster.yaml" language="yaml" title="dagster.yaml" />
3. In the file, fill in the following:
    - `agent_token.env` - The name of the environment variable storing the agent token you created in Step 1.
    - `deployment` - The name of the deployment associated with this instance of the agent. In the preceding example, `prod` was used as the deployment.
4. Save the file.

For more information about `dagster.yaml` configuration options, check out the [`dagster.yaml` reference](/todo).

### Alternative methods for setting the agent token

If you prefer not to specify the agent token by using an environment variable in `dagster.yaml`, pass it to the `dagster-cloud agent run` command:

```bash
dagster-cloud agent run ~/dagster_home/ --agent-token <AGENT_TOKEN>
```

## Step 3: Run the agent

To start the agent, run the following command and pass the path to the `dagster.yaml` file you created in Step 2:

```bash
dagster-cloud agent run ~/dagster_home/
```

To view the agent in Dagster+, click the Dagster icon in the top left to navigate to the **Deployment > Agents** page. You should see the agent running in the **Agent statuses** section:

![Screenshot of Dagster Asset Lineage](/img/placeholder.svg)

## Next steps

- Add a [code location](/todo) to your Dagster+ deployment
