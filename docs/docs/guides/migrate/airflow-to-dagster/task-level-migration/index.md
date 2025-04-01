---
title: 'Migrate from Airflow to Dagster at the task level'
sidebar_position: 30
---

This tutorial demonstrates using [`dagster-airlift`](/api/python-api/libraries/dagster-airlift) to migrate an Airflow DAG to Dagster at the task level.

Using `dagster-airlift` you can:

- Observe Airflow DAGs and their execution history with no changes to Airflow code
- Model and observe assets orchestrated by Airflow with no changes to Airflow code
- Enable a migration process that:
  - Can be done task-by-task in any order with minimal coordination
  - Has task-by-task rollback to reduce risk
  - Retains Airflow DAG structure and execution history during the migration

## Process

In this tutorial, you'll take the following steps:

- **Peer** - During the peer stage, you'll observe an Airflow instance from within a Dagster Deployment using the Airflow REST API. This loads every Airflow DAG as an asset definition and creates a sensor that polls Airflow for execution history.
- **Observe** - In the observe stage, you'll add a mapping that maps the Airflow DAG and task ID to a collection of definitions that you want to observe. (e.g. render the full lineage the dbt models an Airflow task orchestrates). The sensor used for peering also polls for task execution history, and adds materializations to an observed asset when its corresponding task successfully executes.
- **Migrate** - Finally, in the migrate stage, you'll selectively move execution of Airflow tasks to Dagster assets.

## Next steps

To get started with this tutorial, follow the [setup steps](/guides/migrate/airflow-to-dagster/task-level-migration/setup) to install the example code, set up a local environment, and run Airflow locally.

:::tip Migration best practices

When migrating Airflow DAGs to Dagster, we recommend a few best practices:

- **Create separate packages for the Airflow and Dagster deployments.** Airflow has complex dependencies and can be difficult to install in the same environment as Dagster.
- **Create user acceptance tests in Dagster before migrating.** This will help you catch issues easily during migration.
- **Understand the rollback procedure for your migration.** When proxying execution to Dagster from Airflow, you can always roll back by changing a single line of code in the Airflow DAG.

:::
