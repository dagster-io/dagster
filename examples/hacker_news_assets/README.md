# Hacker News Demo Jobs - Software-Defined Assets Version

This repo used Dagster's experimental software-defined asset APIs to set up a "realistic" example of using dagster in a production world, integrating with
many of its features, including:

- Schedules / Sensors
- Asset Materializations
- IOManagers
- Resources
- Unit Tests
- dbt, snowflake, s3, and pyspark integrations

Feel free to poke around!

#### Note:

Running these jobs for yourself without modifications would be pretty tricky, as many of these
solids and resources are configured for a specific environment, and make use of environment
variables that you will not have set on your machine. This is intended as a point of reference
demonstrating the structure of a more advanced Dagster repo.

## High Level Overview

This repo contains three jobs:

- `hacker_news_api_download`
  - This job downloads events from the Hacker News API, splits them by type, and stores comments
    and stories into their own seperate tables in our Snowflake database.
- `story_recommender`
  - This job reads from the tables that `hacker_news_api_download` writes to, and uses this data
    to train a machine learning model to recommend stories to specific users based on their comment history.
- `activity_stats`
  - This job also uses the tables that the `hacker_news_api_download` produces, this time running a dbt
    project which consumes them and creates aggregated metric tables.

The `hacker_news_api_download` job runs on an hourly schedule, constantly updating the tables with new data.
The `story_recommender` job is triggered by a sensor, which detects when both of its input tables have been updated.
The `activity_stats` job is triggered by a different sensor, which will fire a run whenever `hacker_news_api_download` finishes.

Each job makes use of resources, which allows data to be read from and written to different locations based on the environment.

## Running on your laptop

```
dagit -w workspace_local.yaml
```
