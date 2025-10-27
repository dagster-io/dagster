---
description: Implement CI/CD for your Dagster+ Serverless deployment with GitHub, GitLab, or another Git provider.
sidebar_position: 7210
title: CI/CD in Dagster+ Serverless
tags: [dagster-plus-feature]
---

:::note

This guide only applies to [Dagster+ Serverless deployments](/deployment/dagster-plus/serverless). For Hybrid guidance, see [CI/CD in Dagster+ Hybrid](/deployment/dagster-plus/deploying-code/ci-cd/ci-cd-in-hybrid).

:::

If you're a GitHub or GitLab user, you can use our predefined workflows to deploy and synchronize your code to Dagster+ Serverless. You can also use other Git providers, or a local Git repository with the [dagster-cloud CLI](/api/clis/dagster-cloud-cli) to run your own CI/CD process.

:::note

Using the `Connect to GitHub` or `Connect to GitLab` apps in Dagster+ to configure a Git repository requires the [Organization Admin role](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions) so that the system can provision an [agent token](/deployment/dagster-plus/management/tokens/agent-tokens).

:::

<Tabs groupId="method">
  <TabItem value="GitHub" label="GitHub">

If you're a GitHub user, you can use our GitHub app with GitHub Actions to set up a repository containing basic code and configuration for you consistent with Dagster+ best practices.

Once you have set up the repo, pushing your code changes to the `main` branch will automatically deploy them to your `prod` Serverless [full deployment](/deployment/dagster-plus/deploying-code/full-deployments). Pull requests will create ephemeral [branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments) that you can preview and test in the Dagster+ UI.

:::note If you are importing a Dagster project in an existing GitHub repo

- The repo will need to allow the [Workflow permission](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository) for `Read and write permissions`. Workflow permissions settings can be found in GitHub's `Settings` > `Actions` > `General` > `Workflow permissions`. In GitHub Enterprise, these permissions [are controlled at the Organization level](https://github.com/orgs/community/discussions/57244).

- An initial commit will need to be able to be merged directly to the repo's `main` branch to automatically add the GitHub Actions workflow files. If [branch protection rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches#about-protected-branches) require changes be made through pull requests, this will prevent the automatic setup from completing. You can temporarily disable the branch protection rules and then re-enable them after the automatic setup completes.

:::

  </TabItem>
  <TabItem value="GitLab" label="GitLab">

If you're a GitLab user, you can use our GitLab app to set up a repo containing basic code and CI/CD configuration for you consistent with Dagster+ best practices.

Once you have set up the repo, pushing your code changes to the `main` branch will automatically deploy them to your `prod` Serverless deployment. Merge requests will create ephemeral [branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments) that you can preview and test in the Dagster+ UI.

  </TabItem>
  <TabItem value="Other" label="Other Git providers or local development">

If you don't want to use our automated GitHub/GitLab process, you can use the [`dagster-cloud` command-line CLI](/api/clis/dagster-cloud-cli) in another CI environment or locally.

1. First, create a new project by doing one of the following:

   - Cloning the [Serverless quickstart example](https://github.com/dagster-io/dagster/tree/master/examples/quickstart_etl)
   - [Using the `create-dagster project` command](/guides/build/projects/creating-a-new-project). **Note:** If you create your project from the command line, you will need to add `dagster-cloud` as a dependency in your `pyproject.toml` file and add a `dagster-plus-deploy.yml` workflow file to the `.github/workflows` directory. See the [Serverless quickstart example repo](https://github.com/dagster-io/dagster-cloud-serverless-quickstart) for examples of both.

2. Next, install the [`dagster-cloud` CLI](/api/clis/dagster-cloud-cli/installing-and-configuring) and use the `configure` command to authenticate it to your Dagster+ organization:

   ```shell
   pip install dagster-cloud
   dagster-cloud configure
   ```

You can also configure the `dagster-cloud` tool non-interactively; for more information, see [the `dagster-cloud` installation and configuration docs](/api/clis/dagster-cloud-cli/installing-and-configuring).

3. Finally, deploy your project to Dagster+ using the `serverless` command:

```shell
dagster-cloud serverless deploy-python-executable ./my-project \
  --location-name example \
  --package-name quickstart_etl \
  --python-version 3.12
```

:::note Windows variant

If you are using Windows, you will need to replace the `deploy-python-executable` command with `deploy`:

```shell
dagster-cloud serverless deploy ./my-project \
  --location-name example \
  --package-name quickstart_etl \
  --python-version 3.12
```

:::

</TabItem>
</Tabs>
