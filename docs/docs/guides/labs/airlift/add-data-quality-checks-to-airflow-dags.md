---
title: Add data quality checks to Airflow DAGs
sidebar_position: 400
---

Once you have peered your Airflow DAGs in Dagster, you can add [asset checks](/guides/test/asset-checks) to your Dagster code. In Dagster, asset checks can be used to validate the quality of your data assets, and can provide additional observability and value on top of your Airflow DAG even before you begin migration.

Asset checks can act as user acceptance tests to ensure that any migration steps taken are successful, as well as outlive the migration itself.

import AirliftPrereqs from '@site/docs/partials/\_AirliftPrereqs.md';

## Prerequisites

<AirliftPrereqs />