---
title: Refactoring the Project
description: Refactor the completed project into a structure that is more organized and scalable. 
last_update:
  author: Alex Noonan
---

# Refactoring code

Many engineers generally leave something alone once its working as expected. But the first time you do something is rarely the best implementation of a use case and all projects benefit from incremental improvements.

## Splitting up project structure

Right now the project is contained within one definitions file. This has gotten kinda unwieldy and if we were to add more to the project it would only get more disorganized. So we're going to create separate files for all the different Dagster core concepts: 

- Assets
- schedules
- sensors
- partitions

The final project structure should look like this:
```
dagster-etl-tutorial/
├── data/
│   └── products.csv
│   └── sales_data.csv
│   └── sales_reps.csv
│   └── sample_request/
│       └── request.json
├── etl_tutorial/
│   └── assets.py
│   └── definitions.py
│   └── partitions.py
│   └── schedules.py
│   └── sensors.py
├── pyproject.toml
├── setup.cfg
├── setup.py
```

### Assets

Assets make up a majority of our project and this will be our largest file. 

<CodeExample filePath="guides/tutorials/etl_tutorial_completed/etl_tutorial/assets.py" language="python" lineStart="1" lineEnd="292"/>

### Schedules

The schedules file will only contain the `weekly_update_schedule`.

<CodeExample filePath="guides/tutorials/etl_tutorial_completed/etl_tutorial/schedules.py" language="python" lineStart="1" lineEnd="8"/>

### Sensors

The sensors file will have the job and sensor for the `adhoc_request` asset. 

<CodeExample filePath="guides/tutorials/etl_tutorial_completed/etl_tutorial/sensors.py" language="python" lineStart="1" lineEnd="47"/>

## Adjusting definitions object

Now that we have separate files we need to adjust how the different elements are adding to definitions since they are in separate files 

1. Imports

The Dagster project runs from the root directory so whenever you are doing file references you need to have that as the starting point. 

Additionally, Dagster has functions to load all the assets `load_assets_from_modules` and asset checks `load_asset_checks_from_modules` from a module. 

2. Definitions

To bring our project together copy the following code into your `definitions.py` file:

<CodeExample filePath="guides/tutorials/etl_tutorial_completed/etl_tutorial/definitions.py" language="python" lineStart="1" lineEnd="19"/>

## Quick Validation

If you want to validate that your definitions file loads and validates you can run the `dagster definitions validate` in the same directory that you would run `dagster dev`. This command is useful for CI/CD pipelines and allows you to check that your project loads correctly without starting the webserver. 

## Thats it!

Congratulations! You have completed your first project with Dagster and have an example of how to use the building blocks to build your own data pipelines. 

## Recommended next steps

- Join our [Slack community](https://dagster.io/slack).
- Continue learning with [Dagster University](https://courses.dagster.io/) courses.
- Start a [free trial of Dagster+](https://dagster.cloud/signup) for your own project.