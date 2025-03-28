---
title: 'Testing against production with branch deployments'
sidebar_position: 400
---

:::note
This guide is applicable to Dagster+.
:::

This guide details a workflow to test Dagster code in your cloud environment without impacting your production data. To highlight this functionality, we'll leverage Dagster+ branch deployments and a Snowflake database to:

- Execute code on a feature branch directly on Dagster+
- Read and write to a unique per-branch clone of our Snowflake data

With these tools, we can merge changes with confidence in the impact on our data platform and with the assurance that our code will execute as intended.

Here's an overview of the main concepts we'll be using:

- [Assets](/guides/build/assets/) - We'll define three assets that each persist a table to Snowflake.
- [Ops](/guides/build/ops/) - We'll define two ops that query Snowflake: the first will clone a database, and the second will drop database clones.
- [Graphs](/guides/build/ops/graphs) - We'll build graphs that define the order our ops should run.
- [Jobs](/guides/build/jobs/asset-jobs) - We'll define jobs by binding our graphs to resources.
- [Resources](/guides/build/external-resources/) - We'll use the <PyObject section="libraries" module="dagster_snowflake" object="SnowflakeResource" /> to swap in different Snowflake connections to our jobs depending on environment.
- [I/O managers](/guides/build/io-managers/) - We'll use a Snowflake I/O manager to persist asset outputs to Snowflake.

## Prerequisites

:::note

This guide is an extension of the [Transitioning data pipelines from development to production](/guides/deploy/dev-to-prod) guide, illustrating a workflow for staging deployments. We'll use the examples from this guide to build a workflow atop Dagster+'s branch deployment feature.

:::

To complete the steps in this guide, you'll need:

- A Dagster+ account
- An existing Branch Deployments setup that uses [GitHub actions](/dagster-plus/features/ci-cd/configuring-ci-cd#github) or [Gitlab CI/CD](/dagster-plus/features/ci-cd/configuring-ci-cd#non-github). Your setup should contain a Dagster project set up for branch deployments containing:
  - Either a GitHub actions workflow file (e.g. `.github/workflows/branch-deployments.yaml`) or a Gitlab CI/CD file (e.g. `.gitlab-ci.yml`)
  - Dockerfile that installs your Dagster project
- User permissions in Dagster+ that allow you to [access Branch Deployments](/dagster-plus/features/authentication-and-access-control/rbac/user-roles-permissions)

## Overview

We have a `PRODUCTION` Snowflake database with a schema named `HACKER_NEWS`. In our production cloud environment, we'd like to write tables to Snowflake containing subsets of Hacker News data. These tables will be:

- `ITEMS` - A table containing the entire dataset
- `COMMENTS` - A table containing data about comments
- `STORIES` - A table containing data about stories

To set up a branch deployment workflow to construct and test these tables, we will:

1. Define these tables as [assets](/guides/build/assets/).
2. Configure our assets to write to Snowflake using a different connection (credentials and database name) for two environments: production and branch deployment.
3. Write a job that will clone the production database upon each branch deployment launch. Each clone will be named `PRODUCTION_CLONE_<ID>`, where `<ID>` is the pull request ID of the branch. Then we'll create a branch deployment and test our Hacker News assets against our newly cloned database.
4. Write a job that will delete the corresponding database clone upon closing the feature branch.

## Step 1: Create our assets

In production, we want to write three tables to Snowflake: `ITEMS`, `COMMENTS`, and `STORIES`. We can define these tables as assets as follows:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/development_to_production/assets.py"
  startAfter="start_assets"
  endBefore="end_assets"
/>

As you can see, our assets use an [I/O manager](/guides/build/io-managers/) named `snowflake_io_manager`. Using I/O managers and other resources allow us to swap out implementations per environment without modifying our business logic.

## Step 2: Configure our assets for each environment

At runtime, we'd like to determine which environment our code is running in: branch deployment, or production. This information dictates how our code should execute, specifically with which credentials and with which database.

To ensure we can't accidentally write to production from within our branch deployment, we'll use a different set of credentials from production and write to our database clone.

Dagster automatically sets certain [environment variables](/dagster-plus/deployment/management/environment-variables/built-in) containing deployment metadata, allowing us to read these environment variables to discern between deployments. We can access the `DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT` environment variable to determine the currently executing environment.

Because we want to configure our assets to write to Snowflake using a different set of credentials and database in each environment, we'll configure a separate I/O manager for each environment:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/development_to_production/branch_deployments/repository_v1.py"
  startAfter="start_repository"
  endBefore="end_repository"
/>

Refer to the [Dagster+ environment variables documentation](/dagster-plus/deployment/management/environment-variables/) for more info about available environment variables.

## Step 3: Create jobs to manage database cloning per branch deployment

We'll first need to define a job that clones our `PRODUCTION` database for each branch deployment. Later, in our GitHub actions workflow, we can trigger this job to run upon each redeploy. Each clone will be named `PRODUCTION_CLONE_<ID>` with `<ID>` representing the pull request ID, ensuring each branch deployment has a unique clone. This job will drop a database clone if it exists and then reclone from production, ensuring each redeployment has a fresh clone of `PRODUCTION`:

:::note

<strong> Why use ops and jobs instead of assets? </strong> We'll be writing ops to clone the production database for
each branch deployment and drop the clone once the branch is merged. In this case, we chose to use ops since we are
primarily interested in the task that's being performed: cloning or dropping the database. Additionally, we don't need
asset-specific features for these tasks, like viewing them in the Global Asset Graph.

:::

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/development_to_production/branch_deployments/clone_and_drop_db.py"
  startAfter="start_clone_db"
  endBefore="end_clone_db"
/>

We've defined `drop_database_clone` and `clone_production_database` to utilize the <PyObject section="libraries" object="SnowflakeResource" module="dagster_snowflake" />. The Snowflake resource will use the same configuration as the Snowflake I/O manager to generate a connection to Snowflake. However, while our I/O manager writes outputs to Snowflake, the Snowflake resource executes queries against Snowflake.

We now need to define resources that configure our jobs to the current environment. We can modify the resource mapping by environment as follows:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/development_to_production/branch_deployments/repository_v2.py"
  startAfter="start_resources"
  endBefore="end_resources"
/>

Then, we can add the `clone_prod` and `drop_prod_clone` jobs that now use the appropriate resource to the environment and add them to our definitions:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/development_to_production/branch_deployments/repository_v2.py"
  startAfter="start_repository"
  endBefore="end_repository"
/>

## Step 4: Create our database clone upon opening a branch

<Tabs>
  <TabItem value="Using GitHub Actions">

The `branch_deployments.yml` file located in `.github/workflows/branch_deployments.yml` defines a `dagster_cloud_build_push` job with a series of steps that launch a branch deployment. Because we want to queue a run of `clone_prod` within each deployment after it launches, we'll add an additional step at the end `dagster_cloud_build_push`. This job is triggered on multiple pull request events: `opened`, `synchronize`, `reopen`, and `closed`. This means that upon future pushes to the branch, we'll trigger a run of `clone_prod`. The `if` condition below ensures that `clone_prod` will not run if the pull request is closed:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/development_to_production/branch_deployments/clone_prod.yaml" />

Opening a pull request for our current branch will automatically kick off a branch deployment. After the deployment launches, we can confirm that the `clone_prod` job has run:

![Instance overview](/images/guides/development_to_production/branch_deployments/instance_overview.png)

Alternatively, the logs for the branch deployment workflow can be found in the **Actions** tab on the GitHub pull request.

We can also view our database in Snowflake to confirm that a clone exists for each branch deployment. When we materialize our assets within our branch deployment, we'll now be writing to our clone of `PRODUCTION`. Within Snowflake, we can run queries against this clone to confirm the validity of our data:

![Instance overview](/images/guides/development_to_production/branch_deployments/snowflake.png)

  </TabItem>
  <TabItem value="Using Gitlab CI/CD">

The `.gitlab-ci.yaml` script contains a `deploy` job that defines a series of steps that launch a branch deployment. Because we want to queue a run of `clone_prod` within each deployment after it launches, we'll add an additional step at the end of `deploy`. This job is triggered on when a merge request is created or updated. This means that upon future pushes to the branch, we'll trigger a run of `clone_prod`.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/development_to_production/branch_deployments/clone_prod.gitlab-ci.yml" />

Opening a merge request for our current branch will automatically kick off a branch deployment. After the deployment launches, we can confirm that the `clone_prod` job has run:

![Instance overview](/images/guides/development_to_production/branch_deployments/instance_overview.png)

We can also view our database in Snowflake to confirm that a clone exists for each branch deployment. When we materialize our assets within our branch deployment, we'll now be writing to our clone of `PRODUCTION`. Within Snowflake, we can run queries against this clone to confirm the validity of our data:

![Instance overview](/images/guides/development_to_production/branch_deployments/snowflake.png)

</TabItem>

</Tabs>

## Step 5: Delete our database clone upon closing a branch

<Tabs>
<TabItem value="Using GitHub Actions">

Finally, we can add a step to our `branch_deployments.yml` file that queues a run of our `drop_prod_clone` job:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/development_to_production/branch_deployments/drop_db_clone.yaml" />

</TabItem>
<TabItem value="Using Gitlab CI/CD">

Finally, we can add a step to our `.gitlab-ci.yml` file that queues a run of our `drop_prod_clone` job:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/development_to_production/branch_deployments/drop_db_clone.gitlab-ci.yml" />

</TabItem>
</Tabs>

After merging our branch, viewing our Snowflake database will confirm that our branch deployment step has successfully deleted our database clone.

We've now built an elegant workflow that enables future branch deployments to automatically have access to their own clones of our production database that are cleaned up upon merge!
