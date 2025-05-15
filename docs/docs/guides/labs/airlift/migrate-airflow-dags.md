---
title: Migrate Airflow DAGs to Dagster
sidebar_position: 600
---

import AirliftPreview from '@site/docs/partials/\_AirliftPreview.md';
import AirliftPrereqs from '@site/docs/partials/\_AirliftPrereqs.md';

<AirliftPreview />

TK - conceptual info here

## Prerequisites

<AirliftPrereqs />

:::tip Migration best practices

When migrating Airflow DAGs to Dagster, we recommend a few best practices:

- **Create separate packages for the Airflow and Dagster deployments.** Airflow has complex dependencies and can be difficult to install in the same environment as Dagster.
- **Create user acceptance tests in Dagster before migrating.** This will help you catch issues easily during migration.
- **Understand the rollback procedure for your migration.** When proxying execution to Dagster from Airflow, you can always roll back by changing a single line of code in the Airflow DAG.

:::