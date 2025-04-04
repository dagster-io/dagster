---
layout: Integration
status: published
name: Airlift
title: Dagster & Airlift
sidebar_label: Airlift
excerpt: Easily integrate Dagster and Airflow.
date:
apireflink: https://docs.dagster.io/api/python-api/libraries/dagster-airlift
docslink: https://docs.dagster.io/integrations/libraries/airlift/
partnerlink:
categories:
  - ETL
enabledBy:
enables:
tags: [dagster-supported, other]
sidebar_custom_props:
  logo: images/integrations/airflow.svg
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

Airlift is a toolkit for integrating Dagster and Airflow. Using [`dagster-airflift`](/api/python-api/libraries/dagster-airlift), you can:

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

To get started, see "[Migrate from Airflow to Dagster at the task level](/guides/migrate/airflow-to-dagster/task-level-migration)".

:::note

If you need to migrate at the DAG level, see "[Migrate from Airflow to Dagster at the DAG level](/guides/migrate/airflow-to-dagster/dag-level-migration)".

:::

## Federating execution between Airflow instances with Dagster

You can use Airlift to observe DAGs from multiple Airflow instances, and federate execution between them using Dagster as a centralized control plane.

To get started, see "[Federate execution between Airflow instances with Dagster](/guides/migrate/airflow-to-dagster/federation)".

## Airflow operator migration

You can easily migrate common Airflow operators to Dagster. For more information, see "[Airflow operator migration](/guides/migrate/airflow-to-dagster/airflow-operator-migration)".
