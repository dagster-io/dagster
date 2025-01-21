---
layout: Integration
status: published
name: Airlift
title: Dagster & Airlift
sidebar_label: Airlift
excerpt: Easily integrate Dagster and Airflow.
date:
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-airlift
docslink: https://docs.dagster.io/integrations/airlift
partnerlink:
logo:
categories:
  - ETL
enabledBy:
enables:
tags: [dagster-supported, other]
sidebar_custom_props: 
  logo:
---

Airlift is a toolkit for integrating Dagster and Airflow. Using `dagster-airflift`, you can:

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

To get started, see "[Migrating from Airflow to Dagster](airflow-to-dagster/)".

## Federating execution between Airflow instances with Dagster

You can use Airflit to observe DAGs from multiple Airflow instances, and federate execution between them using Dagster as a centralized control plane.

To get started, see "[Federating execution between Airflow instances with Dagster](federation-tutorial/)".

## Migrating common Airflow operators to Dagster

You can easily migrate common Airflow operators to Dagster. For more information, see the "[Migrating common Airflow operators to Dagster](operator-migration/)".
