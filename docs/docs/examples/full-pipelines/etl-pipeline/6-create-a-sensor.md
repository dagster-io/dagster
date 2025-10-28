---
title: Create a sensor
description: Use sensors to create event driven pipelines
sidebar_position: 70
unlisted: true
---

[Sensors](/guides/automate/sensors) allow you to automate workflows based on external events or conditions, making them useful for event-driven automation, especially in situations where jobs occur at irregular cadences or in rapid succession.

Consider using sensors in the following situations:

- **Event-driven workflows**: When your workflow depends on external events, such as the arrival of a new data file or a change in an API response.
- **Conditional execution**: When you want to execute jobs only if certain conditions are met, reducing unnecessary computations.
- **Real-time processing**: When you need to process data as soon as it becomes available, rather than waiting for a scheduled time.

In this step you will:

- Create an asset that runs based on an event-driven workflow
- Create a sensor to listen for conditions to materialize the asset

## 1. Create an event-driven asset

For our pipeline, we want to model a situation where an executive wants a pivot table report of sales results by department and product. They want that processed in real time from their request.

For this asset, we need to define the structure of the request that it is expecting in the materialization context.

Other than that, defining this asset is the same as our previous assets. Copy the following code beneath `product_performance`.

<CodeExample
  path="docs_projects/project_etl_tutorial/src/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_adhoc_request_asset"
  endBefore="end_adhoc_request_asset"
  title="src/etl_tutorial/defs/assets.py"
/>

## 2. Build the sensor

To define a sensor in Dagster, use the `@sensor` decorator. This decorator is applied to a function that evaluates whether the conditions for triggering a job are met.

Sensors include the following elements:

- **Target** or **job**: The target (asset) or job that the sensor will trigger when the conditions are met.
- **RunRequest**: An object that specifies the configuration for the job run. It includes a `run_key` to ensure idempotency and a `run_config` for job-specific settings.

First we will use `dg` to create the sensor file:

<CliInvocationExample path="docs_projects/project_etl_tutorial/commands/dg-scaffold-sensors.txt" />

Now copy the following sensor code in the `sensors.py` file:

<CodeExample
  path="docs_projects/project_etl_tutorial/src/etl_tutorial/defs/sensors.py"
  language="python"
  title="src/etl_tutorial/defs/sensors.py"
/>

## 3. Materialize the sensor asset

1. Reload your Definitions.
2. Navigate to the Automation page.
3. Turn on the `adhoc_request_sensor`.
4. Click on the `adhoc_request_sensor` details.

{/* TODO: Screenshot */}

5. Create a `data/requests` directory in `dagster_tutorial`. Then include a `request.json` file:

```json
{
  "department": "South",
  "product": "Driftwood Denim Jacket",
  "start_date": "2024-01-01",
  "end_date": "2024-06-05"
}
```

6. Click on the green tick to see the run for this request.

{/* TODO: Screenshot */}

## Summary

One new files have been added to the `etl_tutorial` module, `sensors.py`:

<CliInvocationExample path="docs_projects/project_etl_tutorial/tree/step-6.txt" />

Sensors provide a fine grained way to build event driven systems. Combined with declarative automation, there are a number of ways to automate your pipelines.

# Next steps

- Continue this tutorial to [visualize data](/examples/full-pipelines/etl-pipeline/visualize-data)
