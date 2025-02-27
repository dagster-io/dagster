---
title: 'Airflow to Dagster'
sidebar_position: 10
---

## Overview

TK

## Migration best practices

When migrating Airflow DAGs to Dagster, we recommend a few best practices:

- **Create separate packages for the Airflow and Dagster deployments.** Airflow has complex dependencies and can be difficult to install in the same environment as Dagster.
- **Create user acceptance tests in Dagster before migrating.** This will help you catch issues easily during migration.
- **Understand the rollback procedure for your migration.** When proxying execution to Dagster from Airflow, you can always rollback with a single line-of-code change in the Airflow DAG.

## Next steps

* [Migrate from Airflow to Dagster at the task level](task-level-migration/)
* [Migrate from Airflow to Dagster at the DAG level](dag-level-migration/)
* [Federate execution between Airflow instances with Dagster](federation/)