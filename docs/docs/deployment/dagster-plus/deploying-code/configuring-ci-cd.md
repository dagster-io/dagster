---
title: Configuring CI/CD in Dagster+
sidebar_label: CI/CD
description: Implement CI/CD for your Dagster+ Serverless or Hybrid deployment with GitHub, GitLab, or another CI/CD provider.
sidebar_position: 30
tags: [dagster-plus-feature]
---

import UpdateGitHubActionVersion from '@site/docs/partials/_UpdateGitHubActionVersion.md';
import GitHubPrereqs from '@site/docs/partials/_GitHubPrereqs.md';
import GitLabPrereqs from '@site/docs/partials/_GitLabPrereqs.md';

Follow the steps below to create a GitHub or GitLab CI/CD configuration file in your project to deploy and synchronize your code to Dagster+. You can also use other Git providers, or a local Git repository to run your own CI/CD process.

:::info A note on Dagster+ Serverless

When you sign up for Dagster+ Serverless, you create a GitHub or GitLab repository that contains basic Dagster project code and a CI/CD workflow file consistent with Dagster+ best practices.

Pushing changes to the `main` branch of that project repository will automatically deploy them to Dagster+. Pull or merge requests will create ephemeral [branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments) that you can preview and test in the Dagster+ UI.

**To add another Dagster project to your Serverless deployment**, follow the steps in this guide to scaffold a GitHub or GitLab CI/CD configuration file in your new project to deploy and synchronize your code to Dagster+ Serverless. You can also use other Git providers or a local Git repository with the `dagster-cloud` CLI to run your own CI/CD process.

:::

## GitHub

<GitHubPrereqs />

1.  Change to the project root directory:

    ```shell
    cd <project-directory>
    ```

2.  Activate the virtual environment:

    <Tabs>
      <TabItem value="macos" label="MacOS/Unix">
        ```shell source .venv/bin/activate ```
      </TabItem>
      <TabItem value="windows" label="Windows">
        ```shell .venv\Scripts\activate ```
      </TabItem>
    </Tabs>

3.  Add the `dagster-cloud` package as a project dependency:

    <Tabs groupId="package-manager">
      <TabItem value="uv" label="uv">
        <CliInvocationExample path="docs_snippets/docs_snippets/dagster-plus/deployment/ci-cd/uv-add-dagster-cloud.txt" />
      </TabItem>
      <TabItem value="pip" label="pip">
        <CliInvocationExample path="docs_snippets/docs_snippets/dagster-plus/deployment/ci-cd/pip-install-dagster-cloud.txt" />
      </TabItem>
    </Tabs>

4.  Initialize a Git repository in the project directory:

    ```shell
    git init .
    ```

5.  Create a remote repository on GitHub to connect with the local project repository. Be sure to select `Push an existing local repository to github.com` when prompted:

    ```shell
    gh repo create
    ```

6.  Use the [`dg plus deploy configure` CLI command](/api/clis/dg-cli/dg-plus#configure) to scaffold deployment configuration files for your deployment type, including a GitHub Actions workflow file:

    ```shell
    dg plus deploy configure --git-provider github
    ```

7.  Create a Dagster Cloud API token and set it as a GitHub Action secret for the project:

    ```shell
    dg plus create ci-api-token --description 'Used in my-project GitHub Actions' | gh secret set DAGSTER_CLOUD_API_TOKEN
    ```

8.  Commit and push your changes to deploy to Dagster+:

    ```shell
    git add . && git commit -m "Deploy to Dagster+" && git push origin main
    ```

During the deployment, the agent will attempt to load your code and update the metadata in Dagster+. When that has finished, you should see the GitHub Action complete successfully, and also be able to see the code location under the **Deployment** tag in Dagster+.

<UpdateGitHubActionVersion />

## GitLab

<GitLabPrereqs />

1.  Change to the project root directory:

    ```shell
    cd <project-directory>
    ```

2.  Activate the virtual environment:

    - **MacOS/Unix:**
      ```shell
      source .venv/bin/activate
      ```
    - **Windows:**
      ```shell
      .venv\Scripts\activate
      ```

3.  Initialize a Git repository in the project directory:

    ```shell
    git init .
    ```

4.  Commit and push your changes:

    ```shell
    git add . && git commit -m "Initial commit"
    ```

5.  Create a remote repository on GitLab and push your changes to it. You can either do so in the GitLab UI by navigating to the [new project creation page](https://gitlab.com/projects/new#blank_project), or on the command line by running the following command, replacing USERNAME with your GitLab username or organization workspace:

    ```shell
    git push --set-upstream git@gitlab.com:USERNAME/$(git rev-parse --show-toplevel | xargs basename).git $(git rev-parse --abbrev-ref HEAD)
    ```

6.  Use the [`dg plus deploy configure` CLI command](/api/clis/dg-cli/dg-plus#configure) to scaffold deployment configuration files for your deployment type, including a GitLab CI/CD configuration file:

    ```shell
    dg plus deploy configure --git-provider gitlab
    ```

7.  Create a Dagster Cloud API token:

    ```shell
    dg plus create ci-api-token --description 'Used in Dagster project GitHub Actions'
    ```

8.  Set the Dagster Cloud API token as a CI/CD variable in the GitLab repo:
    - Navigate to the project page in GitLab.
    - In the left sidebar, click **Settings** > **CI/CD**.
    - On the settings page, click **Variables**.
    - Under **Project variables**, click **Add variable**.
    - In the **Key** field, enter `DAGSTER_CLOUD_API_TOKEN`
    - In the **Value** field, paste the Dagster Cloud API token.
    - Optionally update the variable type, environments, visibility, flags, and description fields as needed.
    - Click **Add variable**.

After following these steps, commiting and pushing additional changes to your Dagster project in GitLab will deploy them to your Dagster+ organization.

## Other Git providers or local Git repository

<Tabs>
<TabItem value="serverless" label="Dagster+ Serverless">

:::info Prerequisites

Before following the steps in this section, you must first [create a Dagster project](/guides/build/projects/creating-projects).

:::

If you don't want to use our automated GitHub/GitLab process, you can use the [`dagster-cloud` command-line CLI](/api/clis/dagster-cloud-cli) in another CI environment or locally.

1. First, [create a new project with the `create-dagster project` command](/guides/build/projects/creating-projects) and activate the project virtual environment.

2. Next, install the [`dagster-cloud` CLI](/api/clis/dagster-cloud-cli/installing-and-configuring) and use the `configure` command to authenticate it to your Dagster+ organization:

   ```shell
   pip install dagster-cloud
   dagster-cloud configure
   ```

You can also configure the `dagster-cloud` tool non-interactively; for more information, see [the `dagster-cloud` installation and configuration docs](/api/clis/dagster-cloud-cli/installing-and-configuring). For new projects, consider using the `dg` CLI command `dg plus login` instead.

3. Finally, deploy your project to Dagster+ using the `serverless` command, replacing `YOUR_PACKAGE_NAME` with the name of your Dagster package:

```shell
dagster-cloud serverless deploy-python-executable ./my-project \
  --location-name example \
  --package-name YOUR_PACKAGE_NAME \
  --python-version 3.12
```

:::note Windows variant

If you are using Windows, you will need to replace the `deploy-python-executable` command with `deploy`:

```shell
dagster-cloud serverless deploy ./my-project \
  --location-name example \
  --package-name YOUR_PACKAGE_NAME \
  --python-version 3.12
```

:::

</TabItem>
<TabItem value="hybrid" label="Dagster+ Hybrid">

If you are using a non-GitHub CI/CD provider, your system should use the [`dg deploy` command](/api/clis/dg-cli/dg-plus#deploy) to deploy code locations to Dagster+.

:::info Prerequisites

Before following the steps in this section, you must:

- [Create a Dagster project](/guides/build/projects/creating-projects)
- Scaffold deployment configuration files (Dockerfile, `build.yaml`, `containter_context.yaml`) in the project root directory with `dg plus deploy configure`
- Log in to your Dagster organization with `dg plus login`

:::

1.  Set the build environment variables. Note that all variables are required:
    - `DAGSTER_CLOUD_ORGANIZATION`: The name of your organization in Dagster+.
    - `DAGSTER_CLOUD_API_TOKEN`: A Dagster+ API token. **Note:** This is a sensitive value and should be stored as a CI/CD secret if possible.
    - `DAGSTER_BUILD_STATEDIR`: A path to a blank or non-existent temporary directory on the build machine that will be used to store local state during the build.
2.  Initialize the build session:

    ```shell
    dg plus deploy start --deployment=DEPLOYMENT_NAME --project-dir=.
    ```

    This reads the `build.yaml` configuration and initializes the DAGSTER_BUILD_STATEDIR.

3.  Build and upload Docker images for your code locations:

    ```shell
    dg plus deploy build-and-push
    ```

    This command will upload to the registry specified in `build.yaml`. The upload step is specific to your Docker container registry and will require authentication. For more information and a full list of command options, see the [`dg plus deploy build-and-push` API docs](/api/clis/dg-cli/dg-plus#build-and-push).

4.  Deploy to Dagster+:

    ```shell
    dg plus deploy
    ```

    This command updates the code locations in Dagster+. Once this finishes successfully, you should be able to see the code locations under the **Deployments** tab in Dagster+.

:::note

Creating branch deployments using the CLI requires some additional steps. For more information, see [Setting up branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments/configuring-branch-deployments).

:::

</TabItem>
</Tabs>
