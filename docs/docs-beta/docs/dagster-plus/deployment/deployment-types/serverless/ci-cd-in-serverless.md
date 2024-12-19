---
title: 'CI/CD in Serverless'
sidebar_position: 300
---

If you're a GitHub or GitLab user, you can use our predefined workflows to seamlessly deploy and synchronize your code to Dagster+. You can also use other Git providers or a local Git repository with our [dagster-cloud CLI](/dagster-plus/deployment/management/dagster-cloud-cli) to run your own CI/CD process.

<Tabs groupId="method">
<TabItem value="GitHub" label="With GitHub">

If you're a GitHub user, with a single click our GitHub app with GitHub Actions can set up a repo containing skeleton code and configuration for you consistent with Dagster+'s best practices. Pushing your code changes to the `main` branch will automatically deploy them to your `prod` Serverless deployment. Pull requests will spin up ephemeral [branch deployments](/dagster-plus/features/ci-cd/branch-deployments/index.md) that you can view in the Dagster+ UI for previewing and testing.

:::note
**If you are importing a Dagster project that's in an existing GitHub repo:**

- The repo will need to allow the [Workflow permission](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository) for `Read and write permissions`. Workflow permissions settings can be found in GitHub's `Settings` > `Actions` > `General` > `Workflow permissions`. In GitHub Enterprise, these permissions [are controlled at the Organization level](https://github.com/orgs/community/discussions/57244).

- An initial commit will need to be able to be merged directly to the repo's `main` branch to automatically add the GitHub Actions workflow files. If [branch protection rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches#about-protected-branches) require changes be done through a pull request, it will prevent the automatic setup from completing.

  - You can temporarily disable the branch protection rules and then re-enable them after the automatic setup completes.

:::

</TabItem>

<TabItem value="GitLab" label="With GitLab">

If you're a GitLab user, with a single click our GitLab app can set up a repo containing skeleton code and CI/CD configuration for you consistent with Dagster+'s best practices. Pushing your code changes to the `main` branch will automatically deploy them to your `prod` Serverless deployment. Pull requests will spin up ephemeral [branch deployments](/dagster-plus/features/ci-cd/branch-deployments/index.md) that you can view in the Dagster+ UI for previewing and testing.

</TabItem>

<TabItem value="Other" label="Other Git providers or local development">

If you don't want to use our automated GitHub/GitLab process, we offer [the powerful `dagster-cloud` command-line interface (CLI)](/dagster-plus/features/ci-cd/branch-deployments/dagster-cloud-cli) that you can use in another CI environment or locally.

First, [create a new project](/getting-started/quickstart) with the Dagster open source CLI.

The example below uses our [quickstart_etl example project](https://github.com/dagster-io/dagster/tree/master/examples/quickstart_etl). For more info about the examples, visit the [Dagster GitHub repository](https://github.com/dagster-io/dagster/tree/master/examples).

```shell
pip install dagster
dagster project from-example \
  --name my-dagster-project \
  --example quickstart_etl
```

:::note
If using a different project, ensure that `dagster-cloud` is included as a dependency in your `setup.py` or `requirements.txt` file.

For example, in `my-dagster-project/setup.py`:

```python
install_requires=[
    "dagster",
    "dagster-cloud",    # add this line
    ...
]
```

:::

Next, install the [`dagster-cloud` CLI](/dagster-plus/features/ci-cd/branch-deployments/dagster-cloud-cli) and use its `configure` command to authenticate it to your Dagster+ organization.

**Note:** The CLI requires a recent version of Python 3 and Docker.

```shell
pip install dagster-cloud
dagster-cloud configure
```

You can also configure the `dagster-cloud` tool non-interactively; see [the CLI docs](/dagster-plus/features/ci-cd/branch-deployments/dagster-cloud-cli) for more information.

Finally, deploy your project to Dagster+ using the `serverless` command:

```shell
dagster-cloud serverless deploy-python-executable ./my-dagster-project \
  --location-name example \
  --package-name quickstart_etl \
  --python-version 3.12
```

**Note:** Windows users should use the `deploy` command instead of `deploy-python-executable`.

</TabItem>
</Tabs>
