---
description: With Branch Deployments, Dagster+ creates a corresponding branch deployment for each pull request to show what production will look like after the change is merged.
sidebar_position: 20
title: Branch deployments
---

:::note

Branch Deployments are only available in Dagster+.

:::

Dagster+ provides out-of-the-box support for Continuous Integration (CI) with **Branch Deployments**.

Branch Deployments automatically create staging environments of your Dagster code, right in Dagster+. For every push to a branch in your git repository, Dagster+ will create a unique deployment, allowing you to preview the changes in the branch in real-time.

Think of a branch deployment as a branch of your data platform, one where you can preview changes without impacting production or overwriting a testing environment.

Branch deployments offer the following benefits:

- **Improved collaboration.** Branch Deployments make it easy for everyone on your team to stay in the loop on the latest Dagster changes.
- **Reduced development cycle.** Quickly test and iterate on your changes without impacting production or overwriting a testing environment.

## Supported platforms

Branch Deployments can be used with any Git or CI provider. However, setup is easiest with the Dagster GitHub app or Dagster Gitlab app, as parts of the process are automated. For more information, see [Setting up branch deployments](/dagster-plus/features/ci-cd/branch-deployments/setting-up-branch-deployments).

## Change tracking

When a branch deployment is deployed, it compares the asset definitions in the branch deployment with the asset definitions in the main deployment. The Dagster UI will then mark the changed assets, making it easy to identify changes. For more information, see [Change tracking in branch deployments](/dagster-plus/features/ci-cd/branch-deployments/change-tracking).

## Branch deployment example

Below is an example branch deployment setup:

![Overview of branch deployment architecture](/images/dagster-plus/features/branch-deployments/branch-deployments.png)

1. In your git repository, a new branch is created off of `main`. In the example above, this branch is named `feature-1`.

2. Dagster+ is notified of the push and creates a branch deployment named `feature-1`. The branch deployment functions just like your `production` deployment of Dagster+, but contains the Dagster code changes from the `feature-1` branch.

   In this example, the `feature-1` branch deployment 'talks' to a `cloned schema` in a database. This is completely separate from the `prod schema` associated with the `production` deployment.

3. For every push to the `feature-1` branch, the `feature-1` branch deployment in Dagster+ is rebuilt and redeployed.
