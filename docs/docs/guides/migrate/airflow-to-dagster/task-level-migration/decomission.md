---
title: "Decommission the Airflow DAG"
sidebar_position: 500
---

Previously, we completed migration of our Airflow DAG to Dagster assets. If you haven't finished that stage yet, please follow along [here](migrate).

Once we are confident in our migrated versions of the tasks, we can decommission the Airflow DAG. First, we can remove the DAG from our Airflow DAG directory.

Next, we can strip the task associations from our Dagster definitions. This can be done by removing the `assets_with_task_mappings` call. We can use this opportunity to attach our assets to a `ScheduleDefinition` so that Dagster's scheduler can manage their execution:

<CodeExample path="airlift-migration-tutorial/tutorial_example/dagster_defs/stages/standalone.py" language="python"/>