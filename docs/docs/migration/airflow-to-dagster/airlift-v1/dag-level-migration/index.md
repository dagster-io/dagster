---
description: Mapping assets to a full Airflow DAG using dagster-airlift.
sidebar_position: 20
title: Migrate from Airflow to Dagster at the DAG level
canonicalUrl: '/migration/airflow-to-dagster/airlift-v1/dag-level-migration'
slug: '/migration/airflow-to-dagster/airlift-v1/dag-level-migration'
---

import UseAirliftComponent from '@site/docs/partials/\_UseAirliftComponent.md';

<UseAirliftComponent />

This tutorial demonstrates mapping assets to a full Airflow DAG using [`dagster-airlift`](/integrations/libraries/dagster-airlift).

You might want to map assets to a full Airflow DAG rather than on a per-task basis because:

- You're making use of "dynamic tasks" in Airflow, which don't conform neatly to the task mapping protocol in the [task-level migration guide](/migration/airflow-to-dagster/airlift-v1/task-level-migration).
- You want to refactor the DAG structure in a way that doesn't conform to the existing task structure.

## Next steps

To get started with this tutorial, follow the [setup steps](/migration/airflow-to-dagster/airlift-v1/dag-level-migration/setup) to install the example code, set up a local environment, and run Airflow locally.

:::tip Migration best practices

When migrating Airflow DAGs to Dagster, we recommend a few best practices:

- **Create separate packages for the Airflow and Dagster deployments.** Airflow has complex dependencies and can be difficult to install in the same environment as Dagster.
- **Create user acceptance tests in Dagster before migrating.** This will help you catch issues easily during migration.
- **Understand the rollback procedure for your migration.** When proxying execution to Dagster from Airflow, you can always roll back by changing a single line of code in the Airflow DAG.

:::
