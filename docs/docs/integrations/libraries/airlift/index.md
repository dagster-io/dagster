---
title: Dagster & Airlift
sidebar_label: Airlift
description: Airlift is a toolkit for integrating Dagster and Airflow.
tags: [dagster-supported, other]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-airlift
pypi: https://pypi.org/project/dagster-airlift/
sidebar_custom_props:
  logo: images/integrations/airflow.svg
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

import UseAirliftComponent from '@site/docs/partials/\_UseAirliftComponent.md';

<UseAirliftComponent />

<p>{frontMatter.description}</p>

Using [`dagster-airflift`](/integrations/libraries/airlift/dagster-airlift), you can:

- Observe Airflow instances from within Dagster
- Accelerate the migration of Airflow DAGs to Dagster assets with opinionated tooling

## Compatibility

### REST API Availability

Airlift depends on the availability of Airflow’s REST API. Airflow’s REST API was made stable in its 2.0 release (Dec 2020) and was introduced experimentally in 1.10 in August 2018. Currently Airflow requires the availability of the REST API.

- **OSS:** Stable as of 2.00
- **MWAA**
  - Note: only available in Airflow 2.4.3 or later on MWAA.
- **Cloud Composer:** No limitations as far as we know.
- **Astronomer:** No limitations as far as we know.

## Migrating from Airflow to Dagster

You can use Airlift to migrate an Airflow DAG to Dagster assets. Airlift enables a migration process that

- Can be done task-by-task in any order with minimal coordination
- Has task-by-task rollback to reduce risk
- Retains Airflow DAG structure and execution history during the migration

To get started, see "[Migrate from Airflow to Dagster at the task level](/migration/airflow-to-dagster/airlift-v1/task-level-migration)".

:::note

If you need to migrate at the DAG level, see "[Migrate from Airflow to Dagster at the DAG level](/migration/airflow-to-dagster/airlift-v1/dag-level-migration)".

:::

## Federating execution between Airflow instances with Dagster

You can use Airlift to observe DAGs from multiple Airflow instances, and federate execution between them using Dagster as a centralized control plane.

To get started, see "[Federate execution between Airflow instances with Dagster](/migration/airflow-to-dagster/airlift-v1/federation)".

## Airflow operator migration

You can easily migrate common Airflow operators to Dagster. For more information, see "[Airflow operator migration](/migration/airflow-to-dagster/airflow-operator-migration)".
