# Hacker News Demo Pipelines

This repo is set up as a "realistic" example of using dagster in a production world, integrating with
many of its features, including:

- Schedules / Sensors
- Asset Materializations
- IOManagers
- Modes / Resources
- Unit Tests
- dbt, snowflake, s3, and pyspark integrations

Feel free to poke around!

#### Note:

Running these pipelines for yourself without modifications would be pretty tricky, as many of
these solids and resources are configured for a specific environment, and make use of environment
variables that you will not have set on your machine. This is intended as a point of reference
demonstrating the structure of a more advanced Dagster repo.

## High Level Overview

This repo contains two pipelines:

- `download_pipeline`
  - This pipeline downloads events from the Hacker News API, splits them by type, and stores comments
    and stories into their own seperate tables in our Snowflake database.
- `story_recommender`
  - This pipeline reads from the tables that the `download_pipeline` writes to, and uses this data
    to train a machine learning model to recommend stories to specific users based on their comment history.
- `dbt_pipeline`
  - This pipeline also uses the tables that the `download_pipeline` produces, this time running a dbt
    project which consumes them and creates aggregated metric tables.

The `download_pipeline` runs on an hourly schedule, constantly updating the tables with new data.
The `story_recommender` is triggered by a sensor, which detects when both of its input tables have been updated.
The `dbt_pipeline` is triggered by a different sensor, which will fire a run whenever the `download_pipeline` finishes.

Each pipeline has modes that allow them to be run in either a staging (or dev) environment, which will
read data from the same sources as the production modes of these pipelines, but writes data to a different
location than the production pipelines would.
