---
title: Decommission Airflow DAGs after migration
sidebar_position: 700
---

import AirliftPreview from '@site/docs/partials/\_AirliftPreview.md';

<AirliftPreview />

Once you have [migrated your Airflow DAGs to Dagster](/guides/labs/airlift/migrate-airflow-dags) and are confident in your migrated versions of Airflow tasks, you can decommission your Airflow DAG.

## Steps

First, remove the DAG from your Airflow DAG directory.

Next, remove the task associations from your Dagster definitions by removing the <PyObject section="libraries" module="dagster_airlift" object="core.assets_with_task_mappings" displayText="assets_with_task_mappings" /> call.

Finally, attach your assets to a <PyObject section="schedules-sensors" module="dagster" object="ScheduleDefinition" /> so Dagster's scheduler can manage their execution.