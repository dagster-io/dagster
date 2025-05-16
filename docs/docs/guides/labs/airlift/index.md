---
title: Airlift v2
sidebar_position: 30
description: Airflow allows Dagster to connect to live Airflow instances through Airflow’s REST API to observe Airflow executions as they happen, allowing you to easily transition the operation of Airflow pipelines into Dagster, or use Dagster as the control plane across multiple Airflow instances.
---

import AirliftPreview from '@site/docs/partials/\_AirliftPreview.md';

<AirliftPreview />

To get started with Airlift:
* Follow the [setup guide](/guides/labs/airlift/setup)
* [Peer your Airflow instance to Dagster](/guides/labs/airlift/peer-airflow-to-dagster)

After you have peered your Airflow instance to Dagster, follow the guides below that address your organization's needs. These are standalone guides that can be followed in any order:

* [Represent your Airflow DAGs in Dagster](/guides/labs/airlift/represent-airflow-dags-in-dagster)
* [Materialize Dagster assets from Airflow runs](/guides/labs/airlift/materialize-dagster-assets-from-airflow-runs)
* [Add data quality checks to Airflow DAGs](/guides/labs/airlift/add-data-quality-checks-to-airflow-dags)
* [Observe your Airflow DAGs from Dagster](/guides/labs/airlift/observe-airflow-dags-from-dagster)
* [Migrate your Airflow DAGs to Dagster](/guides/labs/airlift/migrate-airflow-dags)
