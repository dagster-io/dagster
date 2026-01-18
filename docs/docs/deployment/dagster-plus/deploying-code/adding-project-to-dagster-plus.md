---
title: Adding a project to Dagster+
sidebar_position: 30
tags: [dagster-plus-feature]
description: You can add a single Dagster project manually to your Dagster+ deployment or add multiple Dagster projects that roll up into one global lineage graph.
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

This guide will cover three options for adding a new Dagster project (also known as a code location) to your Dagster+ deployment:

- [Adding a Dagster project manually](#adding-a-new-dagster-project-manually)
- [Adding a Dagster project in a new Git repository](#adding-a-dagster-project-in-a-new-git-repository)
- [Adding a new Dagster project to an existing Git monorepo](#adding-a-new-dagster-project-to-a-git-monorepo)

## Prerequisites

Before following the steps in this guide, you will need to:

- [Create a Dagster project](/guides/build/projects/creating-projects).
- Have [Editor, Admin, or Organization Admin permissions in Dagster+](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions).
- Find your Dagster+ deployment type. An administrator can help find this information, or you can locate it by clicking _Deployment > Agents tab_ in the Dagster UI. Dagster+ Serverless organizations will have a _Managed by Dagster+_ label next to the agent.

Adding a project follows two steps:

- For Dagster+ Hybrid, ensuring the Dagster code is in a place accessible by your agent, usually by building a Docker image with your code that's pushed to a registry. For Dagster+ Serverless you can skip this step.
- Notifying Dagster+ of the new or updated code location. This will be done by using the Dagster+ Python client.

Often these two steps are handled by CI/CD connected to your Git repository.

## Adding a new Dagster project manually

### Step 1: Install the `dagster-cloud` Python client

Start by installing the `dagster-cloud` Python client:

<Tabs groupId="package-manager">
   <TabItem value="uv" label="uv">

         ```shell
         uv add dagster-cloud
         ```

   </TabItem>

   <TabItem value="pip" label="pip">

         ```shell
         pip install dagster-cloud
         ```

   </TabItem>
</Tabs>

### Step 2: Authenticate the `dagster-cloud` Python client

Next, authenticate the `dagster-cloud` Python client:

1. In the Dagster+ UI, click the user icon in the upper right corner.
2. Click **Organization settings**, then the **Tokens** tab.
3. Click the **Create user token** button.
4. Copy the token.
5. Set the following environment variables:

   ```bash
   export DAGSTER_CLOUD_ORGANIZATION="organization-name" # if your URL is https://acme.dagster.plus your organization name is "acme"
   export DAGSTER_CLOUD_API_TOKEN="your-token"
   ```

### Step 3: Add your Dagster project

Now add your Dagster project. The following example assumes you are running the command from the top-level working directory of your Dagster project with a project named "dagster_tutorial" structured as a Python module named "dagster_tutorial":

<Tabs groupId="package-manager">

   <TabItem value="uv" label="uv">
   ```shell
    .
    ├── pyproject.toml
    ├── README.md
    ├── src
    │   └── dagster_tutorial
    │       ├── __init__.py
    │       ├── definitions.py
    │       └── defs
    │           └── __init__.py
    ├── tests
    │   └── __init__.py
    └── uv.lock
   ```
   </TabItem>
   <TabItem value="pip" label="pip">
   ```shell
    .
    ├── pyproject.toml
    ├── README.md
    ├── src
    │   └── dagster_tutorial
    │       ├── __init__.py
    │       ├── definitions.py
    │       └── defs
    │           └── __init__.py
    └── tests
        └── __init__.py
   ```
   </TabItem>
</Tabs>

The commands below take two main arguments:

- `module_name` is determined by your code structure
- `location_name` is the unique label for this project used in Dagster+

<Tabs>
<TabItem value="serverless" label="Dagster+ Serverless">

If you are using Dagster+ Serverless, run the following command to add your Dagster project:

```bash
dagster-cloud serverless deploy-python-executable --deployment prod --location-name dagster_tutorial --module-name dagster_tutorial
```

Running the command multiple times with the same location name will _update_ the project. Running the command with a new location name will _add_ a project.

</TabItem>
<TabItem value="hybrid" label="Dagster+ Hybrid">

If you are using Dagster+ Hybrid, make sure you have deployed the code appropriately by:

1. Building a Docker image and pushing it to an image registry.
2. Running the `dg plus deploy configure` command from the Dagster project root to create a `dagster_cloud.yaml` file.

Then run the following command, using the image URI which is available from your registry:

```bash
dagster-cloud deployment add-location --deployment prod --location-name dagster_tutorial --module-name dagster_tutorial --image 764506304434.dkr.ecr.us-west-2.amazonaws.com/hooli-data-science-prod:latest
```

</TabItem>
</Tabs>

After running the command, you can verify the project was deployed by navigating to the _Deployments_ tab on Dagster+.

## Adding a Dagster project in a new Git repository

Adding a project to a Git repository follows the same steps as adding a project manually, but automates those steps by running them through CI/CD. For more information, see [Configuring CI/CD in Dagster+](/deployment/dagster-plus/deploying-code/configuring-ci-cd).

The CI/CD process will add the project to Dagster+, which can be verified by viewing the _Deployments_ tab.

## Adding a new Dagster project to a Git monorepo

Many organizations use a Git monorepo to contain multiple Dagster projects. To add a new Dagster project to a monorepo:

1. [Create a Dagster workspace](/guides/build/projects/workspaces/creating-workspaces) to hold your Dagster projects.
2. Move your existing Dagster project(s) into the `/projects` directory of the workspace. If necessary, [convert the projects](/guides/build/projects/moving-to-components/migrating-project) to the new Dagster project structure.
3. In the `/projects` directory of the workspace, [create a new Dagster project](/guides/build/projects/creating-projects) with the `dagster-create` CLI.
4. Run the `dg plus deploy configure` command in the workspace root to create deployment configuration files for projects that need them.

After following these steps, trigger the CI/CD process to add your project to Dagster+. Navigate to the _Deployments_ tab in Dagster+ to confirm your project was added.

## Next steps

- After adding a code location, you may want to set up [access controls](/deployment/dagster-plus/authentication-and-access-control)
- You may want to add additional configuration to your project. This configuration will vary by agent type, but see examples for [setting default resource limits for Kubernetes](/deployment/dagster-plus/hybrid/kubernetes) or [changing the IAM role for ECS](/deployment/dagster-plus/hybrid/amazon-ecs/configuration-reference).
