---
title: 'Observing multiple Airflow instances (own)'
sidebar_position: 100
---

- Create asset representations of Airflow DAGs in Dagster using `load_airflow_dag_asset_specs`
- Add those assets to a `Definitions` object
- Create a sensor to poll the Airflow instance for new runs
- Add sensor to `Definitions` object
- Test by running your Airflow instance locally and triggering a run