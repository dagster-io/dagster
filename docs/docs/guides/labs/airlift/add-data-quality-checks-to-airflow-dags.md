---
title: Add data quality checks to Airflow DAGs
description: To validate the quality of your data assets, add asset checks to your Dagster code once you have peered your Airflow DAGs in Dagster.
sidebar_position: 400
---

import AirliftPreview from '@site/docs/partials/\_AirliftPreview.md';
import AirliftPrereqs from '@site/docs/partials/\_AirliftPrereqs.md';

<AirliftPreview />

Once you have peered your Airflow DAGs in Dagster, you can add [asset checks](/guides/test/asset-checks) to your Dagster code. In Dagster, asset checks can be used to validate the quality of your data assets, and can provide additional observability and value on top of your Airflow DAG even before you begin migration.

Asset checks can act as user acceptance tests to ensure that any migration steps taken are successful, as well as outlive the migration itself.

## Prerequisites

<AirliftPrereqs />