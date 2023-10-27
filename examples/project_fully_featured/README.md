# Fully Featured Project Example

This is meant to be a full "realistic" demo of Dagster, that takes advantage of many of its features, including:

- Software-defined assets
- Schedules
- Sensors
- IOManagers
- Resources
- dbt, S3, and PySpark integrations
- Lightweight invocation in unit tests

View this example in the Dagster docs at [Fully Featured Project](https://docs.dagster.io/guides/dagster/example_project).

## Getting started

Bootstrap your own Dagster project with this example:

```bash
dagster project from-example --name my-dagster-project --example project_fully_featured
```

To install this example and its Python dependencies, run:

```bash
pip install -e ".[dev]"
```

Once you've done this, you can run:

```
dagster-webserver
```

to view this example in Dagster's UI.

## Asset groups

It contains three asset groups:

- `core`
  - Contains data sets of activity on Hacker News, fetched from the Hacker News API. These are partitioned by hour and updated every hour.
- `recommender`
  - A machine learning model that recommends stories to specific users based on their comment history, as well as the features and training set used to fit that model. These are dropped and recreated whenever the core assets receive updates.
- `activity_analytics`
  - Aggregate statistics computed about Hacker News activity. dbt models and a Python model that depends on them. These are dropped and recreated whenever the core assets receive updates.

## Environments

This example is meant to be loaded from three deployments:

- A production deployment, which stores assets in S3 and Snowflake.
- A staging deployment, which stores assets in S3 and Snowflake, under a different key and database.
- A local deployment, which stores assets in the local filesystem and DuckDB.

By default, it will load for the local deployment. You can toggle deployments by setting the `DAGSTER_DEPLOYMENT` env var to `prod` or `staging`.
