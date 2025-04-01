---
title: 'Airflow to Dagster'
sidebar_position: 10
---

[Airlift](/integrations/libraries/airlift) is a toolkit for integrating Airflow into Dagster that you can use to migrate and consolidate existing Airflow DAGs into the Dagster control plane.

Airflow allows Dagster to connect to live Airflow instances through Airflow’s REST API to observe Airflow executions as they happen. This makes it easy to transition the operation of Airflow pipelines into Dagster, or use Dagster to act as the control plane across multiple Airflow instances.

A complete Airlift migration works through the following steps:

- **Peer** - View the Airflow instance within Dagster.
- **Observe** - Map the Airflow DAG to a full lineage of assets in Dagster.
- **Migrate** - Move execution of specific Airflow tasks or an entire Airflow DAG to Dagster.
- **Decomission** - Remove your Airflow code and move execution responsibilities over to Dagster.

However, you don't need to complete every step with Airlift, and should tailor the migration process to your organization's needs. You may find immediate value from simply observing Airflow processes in Dagster and building around those workflows. To get started, see the documentation that best fits your situation:

- [Federate execution between multiple Airflow instances with Dagster](federation/)
- [Migrate from a single Airflow instance to Dagster at the DAG level](dag-level-migration/)
- [Migrate from a single Airflow instance to Dagster at the task level](task-level-migration/)
