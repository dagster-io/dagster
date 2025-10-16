---
description: Implement CI/CD for your Dagster+ Serverless deployment with GitHub, GitLab, or another Git provider.
sidebar_position: 7210
title: CI/CD in Dagster+ Serverless
tags: [dagster-plus-feature]
---

:::note

This guide only applies to [Dagster+ Serverless deployments](/deployment/dagster-plus/serverless). For Hybrid guidance, see [CI/CI in Dagster+ Hybrid](/deployment/dagster-plus/deploying-code/ci-cd/ci-cd-in-hybrid).

:::

If you're a GitHub or GitLab user, you can use our predefined workflows to deploy and synchronize your code to Dagster+. You can also use other Git providers or a local Git repository with our [dagster-cloud CLI](/api/clis/dagster-cloud-cli) to run your own CI/CD process.

:::note

Using the `Connect to GitHub` or `Connect to GitLab` buttons in Dagster+ to configure a Git repository requires the [Organization Admin role](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions) so that the system can provision an [agent token](/deployment/dagster-plus/management/tokens/agent-tokens).

:::

<Tabs groupId="method">
<TabItem value="GitHub" label="GitHub">

If you're a GitHub user, you can use our GitHub app with GitHub Actions to set up a repository containing basic code and configuration for you consistent with Dagster+ best practices. Pushing your code changes to the `main` branch will automatically deploy them to your `prod` Serverless deployment. Pull requests will spin up ephemeral [branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments) that you can view in the Dagster+ UI for previewing and testing.

:::note

**If you are importing a Dagster project that's in an existing GitHub repo:**

- The repo will need to allow the [Workflow permission](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository) for `Read and write permissions`. Workflow permissions settings can be found in GitHub's `Settings` > `Actions` > `General` > `Workflow permissions`. In GitHub Enterprise, these permissions [are controlled at the Organization level](https://github.com/orgs/community/discussions/57244).

- An initial commit will need to be able to be merged directly to the repo's `main` branch to automatically add the GitHub Actions workflow files. If [branch protection rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches#about-protected-branches) require changes be done through a pull request, it will prevent the automatic setup from completing.

  - You can temporarily disable the branch protection rules and then re-enable them after the automatic setup completes.

:::

</TabItem>

<TabItem value="GitLab" label="GitLab">

If you're a GitLab user, you can use our GitLab to set up a repo containing basic code and CI/CD configuration for you consistent with Dagster+ best practices. Pushing your code changes to the `main` branch will automatically deploy them to your `prod` Serverless deployment. Pull requests will spin up ephemeral [branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments) that you can view in the Dagster+ UI for previewing and testing.

</TabItem>

<TabItem value="Other" label="Other Git providers or local development">

If you don't want to use our automated GitHub/GitLab process, you can use the [`dagster-cloud` command-lnine CLI](/api/clis/dagster-cloud-cli) in another CI environment or locally.

First, create a new project by doing one of the following:
- [Using the `create-dagster project` command](/guides/build/projects/creating-a-new-project)
- Cloning the [Serverless quickstart example](https://github.com/dagster-io/dagster/tree/master/examples/quickstart_etl)

:::note

If you create your own project with the `create-dagster project` command, ensure that `dagster-cloud` is included as a dependency in your `pyproject.toml` file. For example:

```toml
[project]
name = "your-project-name"
requires-python = ">=3.9,<3.14"
version = "0.1.0"
dependencies = [
    "dagster",
    "dagster-cloud",
]
```

:::

Next, install the [`dagster-cloud` CLI](/api/clis/dagster-cloud-cli/installing-and-configuring) and use its `configure` command to authenticate it to your Dagster+ organization.

```shell
pip install dagster-cloud
dagster-cloud configure
```

:::info

The `dagster-cloud` CLI requires a recent version of Python 3 and Docker.

:::

You can also configure the `dagster-cloud` tool non-interactively; for more information, see [the `dagster-cloud` installation and configuration docs](/api/clis/dagster-cloud-cli/installing-and-configuring).

Finally, deploy your project to Dagster+ using the `serverless` command:

<Tabs>
  <TabItem value="macos" label="MacOS/Unix">
    ```shell
    dagster-cloud serverless deploy-python-executable ./my-project \
      --location-name example \
      --package-name quickstart_etl \
      --python-version 3.12
    ```
  </TabItem>
  <TabItem value="windows" label="Windows">
    ```shell
    dagster-cloud serverless deploy ./my-project \
      --location-name example \
      --package-name quickstart_etl \
      --python-version 3.12
    ```
  </TabItem>
</Tabs>

</TabItem>
</Tabs>
