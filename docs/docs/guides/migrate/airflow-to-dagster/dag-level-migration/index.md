---
title: 'Migrate from Airflow to Dagster at the DAG level'
sidebar_position: 20
---

Dagster allows you to map assets to a full Airflow DAG instead of one task at a time. You might do this because:

- You're making use of "dynamic tasks" in Airflow, which don't conform neatly to the task mapping protocol in the [task-level migration guide](../task-level-migration/).
- You want to refactor the DAG structure in a way that that doesn't conform to the existing task structure.