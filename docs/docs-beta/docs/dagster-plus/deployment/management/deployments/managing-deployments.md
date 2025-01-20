---
title: "Managing deployments in Dagster+"
---

:::note

This guide is applicable to Dagster+.

:::

In Dagster+, there are two types of deployments:

- [**Branch deployments**](/dagster-plus/features/ci-cd/branch-deployments), which are temporary deployments built for testing purposes.
- **Full deployments**, which are persistent, fully-featured deployments intended to perform actions on a recurring basis.

This guide will focus on **full deployments**, hereafter referred to simply as deployments.

## About deployments

Deployments are standalone environments, allowing you to operate independent instances of Dagster with separately managed permissions.

When a Dagster+ organization is created, a single deployment named `prod` will also be created. To create additional deployments, a [Pro plan](https://dagster.io/pricing) is required.

Each deployment can have one or multiple [code locations](/dagster-plus/managing-deployments/code-locations).

**Concerned about testing environments?** We recommend using Branch Deployments to test your changes, even if you're able to create additional deployments. Branch deployments are available for all Dagster+ users, regardless of plan.

Refer to the [Branch Deployment docs](/dagster-plus/managing-deployments/branch-deployments) for more info, or the [Testing against production using Branch Deployments guide](/guides/dagster/branch_deployments) for a real-world example.

## Viewing and switching deployments

In Dagster+, you can view and switch between deployments using the **deployment switcher**:

![The deployment switcher in Dagster+](/images/dagster-cloud/developing-testing/deployments/deployment-switcher.png)

To view all deployments, click **View all deployments**.

## Creating deployments

:::note

[Organization Admin permissions](/dagster-plus/features/authentication-and-access-control/rbac/user-roles-permissions) are required to create deployments. Additionally, note that creating multiple deployments requires a [Pro plan](https://dagster.io/pricing).

:::

To create a deployment:

1. Sign in to your Dagster+ account.
2. Access the **Deployments** page using one of the following options:
   - Click the **deployment switcher > View all deployments**.
   - Click **your user icon > Organization Settings > Deployments**.
3. Click the **+ New deployment** button.
4. In the modal that displays, fill in the following:
   - **Name** - Enter a name for the deployment.
   - **Initial deployment permissions** - Select the permissions you want to use to create the deployment:
     - **Empty permissions** - Creates the deployment with an empty set of permissions. **Note**: Only Organization Admins will be able to manage the deployment until other uses are granted Admin or Editor permissions.
     - **Copy from** - Creates the deployment using permissions duplicated from an existing deployment.
5. When finished, click **Create deployment**.

## Deleting deployments

:::note

[Organization Admin permissions](/dagster-plus/features/authentication-and-access-control/rbac/user-roles-permissions) are required to delete deployments. Additionally, note that deleting a deployment also deletes all its associated data, including code locations, jobs, schedules, and sensors.

:::

To delete a deployment:

1. Sign in to your Dagster+ account.
2. Access the **Deployments** page using one of the following options:
   - Click the **deployment switcher > View all deployments**.
   - Click the **deployment switcher**, then the **gear icon** next to the deployment.
   - Click **your user icon > Organization Settings > Deployments**.
3. Click the **Delete** button next to the deployment you want to delete.
4. When prompted, confirm the deletion.

## Configuring deployment settings

:::note

[Editor permissions](/dagster-plus/features/authentication-and-access-control/rbac/user-roles-permissions) are required to modify deployment settings.

:::

Deployment settings can be configured in the Dagster+ interface or using the `dagster-cloud` CLI. Refer to the [deployment settings reference](/dagster-plus/managing-deployments/deployment-settings-reference) for more info about individual settings.

<Tabs>
  <TabItem value="Dagster+">
   To configure deployment settings in the Dagster+ UI:

  1. Sign in to your Dagster+ account.
  2. Access the **Deployments** page using one of the following:
    - Click the **deployment switcher > View all deployments**.
    - Click the **deployment switcher**, then the **gear icon** next to the deployment.
    - Click **your user icon > Organization Settings > Deployments**.
  3. Click the **Settings** button next to the deployment you want to configure.
  4. In the window that displays, configure settings for the deployment.
  5. When finished, click **Save deployment settings**.
  </TabItem>
  <TabItem value="dagster-cloud CLI">

:::note

`dagster-cloud` 0.13.14 or later must be installed to run the CLI. Agent and/or job code doesn't need to be upgraded.

:::

Create a file with the settings you'd like to configure. For example:

```yaml
# my-settings.yaml

run_queue:
  max_concurrent_runs: 10
  tag_concurrency_limits:
    - key: "special-runs"
      limit: 5

run_monitoring:
  start_timeout_seconds: 1200
  cancel_timeout_seconds: 1200

run_retries:
  max_retries: 0
```

Use the CLI to upload the settings file:

```shell
dagster-cloud deployment settings set-from-file my-settings.yaml
```

This will replace all of your configured settings. Any that are not specified will resort to their default values. You also use the CLI to read your current settings, including the default values:

```shell
dagster-cloud deployment settings get
```

  </TabItem>
</Tabs>
