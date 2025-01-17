---
title: Refactor your project
description: Refactor your completed project into a structure that is more organized and scalable. 
last_update:
  author: Alex Noonan
sidebar_position: 80
---

Many engineers generally leave something alone once it's working as expected. But the first time you do something is rarely the best implementation of a use case and all projects benefit from incremental improvements.

## Splitting up project structure

Currently, your project is contained in one definitions file. However, this file has gotten fairly complex, and adding to it would only increase its complexity. To fix that, we will create separate files for each core Dagster concept:

- Assets
- Schedules
- Sensors
- Partitions

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

<CodeExample filePath="guides/tutorials/etl_tutorial_completed/etl_tutorial/schedules.py" language="python" />

### Sensors

The sensors file will have the job and sensor for the `adhoc_request` asset. 

<CodeExample filePath="guides/tutorials/etl_tutorial_completed/etl_tutorial/sensors.py" language="python" lineStart="1" lineEnd="47"/>

## Refactoring the Definitions object

Now that we have separate files, we need to adjust how the different elements are added to the Definitions object.

:::note
The Dagster project runs from the root directory, so whenever you reference files in your project, you need to use the root as the starting point.
Additionally, Dagster has functions to load all assets and asset checks from a module (load_assets_from_modules and load_asset_checks_from_modules, respectively).
:::

To bring your project together, copy the following code into your `definitions.py` file:

<CodeExample filePath="guides/tutorials/etl_tutorial_completed/etl_tutorial/definitions.py" language="python" lineStart="1" lineEnd="19"/>

## Quick validation

To validate that your definitions file loads and validates, you can run `dagster definitions validate` in the same directory that you would run `dagster dev`. This command is useful for CI/CD pipelines and allows you to check that your project loads correctly without starting the web server. 

## Thats it!

Congratulations! You have completed your first project with Dagster and have an example of how to use the building blocks to build your own data pipelines. 

## Recommended next steps

- Join our [Slack community](https://dagster.io/slack).
- Continue learning with [Dagster University](https://courses.dagster.io/) courses.
- Start a [free trial of Dagster+](https://dagster.cloud/signup) for your own project.