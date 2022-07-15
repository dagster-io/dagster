# Hacker News Demo

This is meant to be a full "realistic" demo of Dagster, that takes advantage of many of its features, including:

- Software-defined assets
- Schedules
- Sensors
- IOManagers
- Resources
- dbt, S3, and PySpark integrations
- Lightweight invocation in unit tests

Feel free to poke around!

## Running locally

```
# Install the example so that it will be on your Python path
pip install -e .

# Load it in the web UI
dagit -w workspace.yaml
```

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


