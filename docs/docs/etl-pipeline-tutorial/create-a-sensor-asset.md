---
title: Create a sensor asset
description: Use sensors to create event driven pipelines
last_update:
  author: Alex Noonan
sidebar_position: 60
---

[Sensors](/guides/automate/sensors) allow you to automate workflows based on external events or conditions, making them useful for event-driven automation, especially in situations where jobs occur at irregular cadences or in rapid succession.

Consider using sensors in the following situations:

- **Event-driven workflows**: When your workflow depends on external events, such as the arrival of a new data file or a change in an API response.
- **Conditional execution**: When you want to execute jobs only if certain conditions are met, reducing unnecessary computations.
- **Real-time processing**: When you need to process data as soon as it becomes available, rather than waiting for a scheduled time.

In this step you will:

- Create an asset that runs based on a event-driven workflow
- Create a sensor to listen for conditions to materialize the asset

## 1. Create an event-driven asset

For our pipeline, we want to model a situation where an executive wants a pivot table report of sales results by department and product. They want that processed in real time from their request.

For this asset, we need to define the structure of the request that it is expecting in the materialization context.

Other than that, defining this asset is the same as our previous assets. Copy the following code beneath `product_performance`.

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_adhoc_asset"
  endBefore="end_adhoc_asset"
/>

## 2. Build the sensor

To define a sensor in Dagster, use the `@sensor` decorator. This decorator is applied to a function that evaluates whether the conditions for triggering a job are met.

Sensors include the following elements:

- **Job**: The job that the sensor will trigger when the conditions are met.
- **RunRequest**: An object that specifies the configuration for the job run. It includes a `run_key` to ensure idempotency and a `run_config` for job-specific settings.

First we will use `dg` to create the sensor file:

```bash
dg scaffold dagster.sensor sensors.py
```

Now copy the following sensor code in the `defs/sensors.py` file:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/defs/sensors.py"
  language="python"
/>

## 3. Materialize the sensor asset

1. Reload your Definitions.

2. Navigate to the Automation page.

3. Turn on the `adhoc_request_sensor`.

4. Click on the `adhoc_request_sensor` details.

   ![2048 resolution](/images/tutorial/etl-tutorial/sensor-evaluation.png)

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

   ![2048 resolution](/images/tutorial/etl-tutorial/sensor-asset-run.png)

## That's it!

Congratulations! You have completed your first project with Dagster and have an example of how to use the building blocks to build your own data pipelines.

## Recommended next steps

- Join our [Slack community](https://dagster.io/slack).
- Continue learning with [Dagster University](https://courses.dagster.io/) courses.
- Start a [free trial of Dagster+](https://dagster.cloud/signup) for your own project.
