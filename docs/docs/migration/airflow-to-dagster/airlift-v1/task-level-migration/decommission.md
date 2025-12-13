---
description: Decommission an Airflow DAG by removing it from the Airflow directory, removing task associations from Dagster Definitions, and attaching assets to a ScheduleDefinition.
sidebar_position: 500
title: Decommission the Airflow DAG
---

import UseAirliftComponent from '@site/docs/partials/\_UseAirliftComponent.md';

<UseAirliftComponent />

Previously, we completed [migration](/migration/airflow-to-dagster/airlift-v1/task-level-migration/migrate) of our example Airflow DAG to Dagster assets. Once we are confident in our migrated versions of the tasks, we can decommission the Airflow DAG.

First, we can remove the DAG from our Airflow DAG directory.

Next, we can remove the task associations from our Dagster definitions. This can be done by removing the <PyObject section="libraries" integration="airlift" module="dagster_airlift" object="core.assets_with_task_mappings" displayText="assets_with_task_mappings" /> call.

Finally, we can attach our example assets to a <PyObject section="schedules-sensors" module="dagster" object="ScheduleDefinition" /> so Dagster's scheduler can manage their execution.

When you have finished the above steps, your code should look like the following:

<CodeExample path="airlift-migration-tutorial/tutorial_example/dagster_defs/stages/standalone.py" language="python" />
