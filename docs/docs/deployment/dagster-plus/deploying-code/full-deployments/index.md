---
title: Full deployments
sidebar_position: 10
description: Dagster+ full deployments are persistent, fully-featured deployments intended to run pipelines on a recurring basis.
canonicalUrl: '/deployment/dagster-plus/deploying-code/full-deployments'
slug: '/deployment/dagster-plus/deploying-code/full-deployments'
tags: [dagster-plus-feature]
---

Full deployments are independent deployment instances with separately managed permissions within your Dagster deployment. Each full deployment can have one or multiple [code locations](/guides/build/projects).

When a Dagster+ organization is created, a single deployment named `prod` will also be created. To create additional full deployments, you will need to sign up for a [Pro plan](https://dagster.io/pricing).

:::note Full deployments vs branch deployments

In Dagster+, there are two types of deployments:

- [**Branch deployments**](/deployment/dagster-plus/deploying-code/branch-deployments), which are temporary deployments built for testing purposes. We recommend using branch deployments to test your changes, even if you're able to create additional full deployments. Branch deployments are available for all Dagster+ users, regardless of plan.
- **Full deployments**, which are persistent, fully-featured deployments intended to perform actions on a recurring basis. This section of the documentation focuses on full deployments.

:::
