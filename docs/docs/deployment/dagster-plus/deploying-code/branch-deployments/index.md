---
title: Branch deployments
sidebar_position: 30
description: With branch deployments, Dagster+ creates a corresponding ephemeral preview deployment of your Dagster code for each pull or merge request to show what your pipeline will look like after the change is merged.
canonicalUrl: '/deployment/dagster-plus/deploying-code/branch-deployments'
slug: '/deployment/dagster-plus/deploying-code/branch-deployments'
tags: [dagster-plus-feature]
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

Branch deployments automatically create ephemeral preview deployments of your Dagster code, right in Dagster+. Every time you push to a branch with an open pull or merge request in the Git repository for your Dagster code, Dagster+ will redeploy the code in the branch, allowing you to preview the changes to the branch in real time, without affecting production or overwriting a test environment.

## Supported platforms

Branch deployments can be used with any Git or CI provider. However, setup is easiest with the Dagster GitHub Actions or Dagster GitLab CI/CD workflow, as parts of the process are automated. For more information, see [Setting up branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments/setting-up-branch-deployments).

## Change tracking

When a branch deployment is deployed, it compares the asset definitions in the branch deployment with the asset definitions in the main deployment. The Dagster UI will then mark the changed assets, making it easy to identify changes. For more information, see [Change tracking in branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments/change-tracking).

## Branch deployment example

Below is an example branch deployment setup:

![Overview of branch deployment architecture](/images/dagster-plus/features/branch-deployments/branch-deployments.png)

1. In the Git repository, a new branch called `feature-1` is created from the `main` branch, and a pull request is opened from that branch.

2. Dagster+ is notified of the new pull request and creates a branch deployment named `feature-1`. The branch deployment functions just like the `production` deployment of Dagster+, but contains the Dagster code changes from the `feature-1` branch.

   In this example, the `feature-1` branch deployment communicates with a `cloned schema` in a database. This is completely separate from the `prod schema` associated with the `production` deployment.

3. For every push to the `feature-1` branch, the `feature-1` branch deployment in Dagster+ is rebuilt and redeployed.
