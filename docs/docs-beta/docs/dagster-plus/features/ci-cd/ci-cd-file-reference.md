---
title: CI/CD file reference
---

:::note
This reference is applicable to Dagster+.
:::

When you import a project into Dagster+ from GitHub or Gitlab, a few `.yml` files will be added to the repository. These files are essential as they manage the deployments in Dagster+.

## branch_deployments.yml

This file defines the steps required to use [branch deployments](/dagster-plus/features/ci-cd/branch-deployments/). It is required for branch deployments.

:::note

If you are using a [Hybrid deployment](/dagster-plus/deployment/deployment-types/hybrid/), you must manually add `branch_deployments.yml` to the repository.

:::

## deploy.yml

This file is required for Dagster+. It defines the steps required to deploy a project in Dagster+, including running checks, checking out the project directory, and deploying the project. Additionally, note the following:

* **If you are using a [Hybrid deployment](/dagster-plus/deployment/deployment-types/hybrid/)**, you must manually add `deploy.yml` to the repository.
* **If you are using [dbt](/integrations/libraries/dbt)**, you  may need to take additional steps to deploy your project. For more information, see "[Using dbt with Dagster+](/todo).
