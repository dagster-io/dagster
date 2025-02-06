---
title: 'Migrating from Airflow to Dagster'
sidebar_position: 10
---

This tutorial demonstrates using [`dagster-airlift`](/api/python-api/libraries/dagster-airlift) to migrate an Airflow DAG to Dagster.

Using `dagster-airlift` we can:

- Observe Airflow DAGs and their execution history with no changes to Airflow code
- Model and observe assets orchestrated by Airflow with no changes to Airflow code
- Enable a migration process that
  - Can be done task-by-task in any order with minimal coordination
  - Has task-by-task rollback to reduce risk
  - That retains Airflow DAG structure and execution history during the migration

## Process

This is a high level overview of the steps to migrate an Airflow DAG to Dagster:

- **Peer**
  - Observe an Airflow instance from within a Dagster Deployment via the Airflow REST API.
  - This loads every Airflow DAG as an asset definition and creates a sensor that polls Airflow for execution history.
- **Observe**
  - Add a mapping that maps the Airflow DAG and task id to a basket of definitions that you want to observe. (e.g. render the full lineage the dbt models an Airflow task orchestrates)
  - The sensor used for peering also polls for task execution history, and adds materializations to an observed asset when its corresponding task successfully executes
- **Migrate**
  - Selectively move execution of Airflow tasks to Dagster Software Defined Assets
