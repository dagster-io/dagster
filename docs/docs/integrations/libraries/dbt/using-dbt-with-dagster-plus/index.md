---
title: 'Using dbt with Dagster+'
description: Deploy your dbt & Dagster project in Dagster+.
sidebar_position: 400
canonicalUrl: '/integrations/libraries/dbt/using-dbt-with-dagster-plus'
slug: '/integrations/libraries/dbt/using-dbt-with-dagster-plus'
---

Using a dbt project in Dagster+ allows you to automatically load your dbt models as Dagster assets. This can be be done with both deployment options in Dagster+: Serverless and Hybrid.

[Learn more about deployment options in Dagster+](/deployment/dagster-plus).

## Serverless deployments

If you have a Serverless deployment, you can directly import an existing dbt project in Dagster+ when adding a new code location. This can be done with:

- An existing dbt project that is not already using Dagster, or
- A Dagster project in which your dbt project is included

For more information, see "[Importing a dbt project to Dagster+ Serverless](/integrations/libraries/dbt/using-dbt-with-dagster-plus/serverless)".

## Hybrid deployments

If you have a Hybrid deployment, you must make the dbt project accessible to the Dagster code executed by your agent.

- When using Amazon Elastic Container Service (ECS), Kubernetes, or Docker agent, you must include the dbt project in the Docker Image containing your Dagster code.
- When using a local agent, you must make your dbt project accessible to your Dagster code on the same machine as your agent.

For more information, see "[Using dbt with Hybrid deployments in Dagster+](/integrations/libraries/dbt/using-dbt-with-dagster-plus/hybrid)".
