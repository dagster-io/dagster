---
title: 'Migrate from Airflow to Dagster at the DAG level'
sidebar_position: 20
---

There may be DAGs for which you want to migrate the entire DAG at once rather than on a per-task basis. Some reasons for taking this approach:

- You're making use of "dynamic tasks" in Airflow, which don't conform neatly to the task mapping protocol in the task-level migration guide.
- You want to make more substantial refactors to the DAG structure that don't conform to the existing task structure.

For cases like this, we allow you to map assets to a full DAG.
