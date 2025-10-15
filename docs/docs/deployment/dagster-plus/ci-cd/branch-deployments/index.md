---
description: With Branch Deployments, Dagster+ creates a corresponding branch deployment for each pull request to show what production will look like after the change is merged.
sidebar_position: 7300
title: Deploying to staging with branch deployments
canonicalUrl: '/deployment/dagster-plus/ci-cd/branch-deployments'
slug: '/deployment/dagster-plus/ci-cd/branch-deployments'
tags: [dagster-plus-feature]
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

Branch deployments automatically create staging environments of your Dagster code, right in Dagster+. Every time you push to a branch with an open pull request in the Git repository for your Dagster code, Dagster+ will redeploy the code in the branch, allowing you to preview the changes to the branch in real time, without affecting production or overwriting a test environment.

## Supported platforms

Branch deployments can be used with any Git or CI provider. However, setup is easiest with the Dagster GitHub actions or Dagster Gitlab CI/CD workflow, as parts of the process are automated. For more information, see [Setting up branch deployments](/deployment/dagster-plus/ci-cd/branch-deployments/setting-up-branch-deployments).

## Change tracking

When a branch deployment is deployed, it compares the asset definitions in the branch deployment with the asset definitions in the main deployment. The Dagster UI will then mark the changed assets, making it easy to identify changes. For more information, see [Change tracking in branch deployments](/deployment/dagster-plus/ci-cd/branch-deployments/change-tracking).

## Branch deployment example

Below is an example branch deployment setup:

![Overview of branch deployment architecture](/images/dagster-plus/features/branch-deployments/branch-deployments.png)

1. In your Git repository, a new branch is created from the `main` branch. In the example above, this branch is named `feature-1`. A pull request is created from that branch.

2. Dagster+ is notified of the new pull request and creates a branch deployment named `feature-1`. The branch deployment functions just like your `production` deployment of Dagster+, but contains the Dagster code changes from the `feature-1` branch.

   In this example, the `feature-1` branch deployment communicates with a `cloned schema` in a database. This is completely separate from the `prod schema` associated with the `production` deployment.

3. For every push to the `feature-1` branch, the `feature-1` branch deployment in Dagster+ is rebuilt and redeployed.
