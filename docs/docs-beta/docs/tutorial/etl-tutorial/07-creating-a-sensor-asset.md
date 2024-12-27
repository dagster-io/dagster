---
title: Event Driven Assets
description: Use sensors to create event driven pipelines
last_update:
  author: Alex Noonan
---

[Sensors](/guides/automate/sensors) in Dagster are a powerful tool for automating workflows based on external events or conditions. They allow you to trigger jobs when specific criteria are met, making them essential for event-driven automation. 

Event driven automations to support situations where jobs occur at irregular cadences or in rapid succession.  is the building block in Dagster you can use to support this. 

Consider using sensors in the following situations:
- **Event-Driven Workflows**: When your workflow depends on external events, such as the arrival of a new data file or a change in an API response.
- **Conditional Execution**: When you want to execute jobs only if certain conditions are met, reducing unnecessary computations.
- **Real-Time Processing**: When you need to process data as soon as it becomes available, rather than waiting for a scheduled time.

In this step you will:

- Create an asset the runs based on a event driven workflow
- Create a sensor to listen for conditions to materialize the asset. 

## 1. Event Driven Asset

For our pipeline, we want to model a situation where an executive wants a pivot table report of sales results by department and product. They want that processed in real time from their request and it isn't a high priority to build the reporting to have this available and refreshing. 

For this asset we need to define the structure of the request that it is expecting in the materialization context. 

Other than that defining this asset is the same as our previous assets. Copy the following code beneath `product_performance` 

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="274" lineEnd="311"/>

## 2. Build the Sensor

To define a sensor in Dagster, you use the `@sensor` decorator. This decorator is applied to a function that evaluates whether the conditions for triggering a job are met. Here's a basic example:

sensors include the following elements:

- **Job**: The job that the sensor will trigger when the conditions are met.
- **RunRequest**: An object that specifies the configuration for the job run. It includes a `run_key` to ensure idempotency and a `run_config` for job-specific settings.

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="313" lineEnd="355"/>


## 3. Materialize the sensor asset

1. Update definitions object to the following:

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="356" lineEnd="371"/>

2. Reload definitions

3. Navigate to the Automation Page

4. Turn on the `automation_request_sensor`

5. Click on the `automation_request_sensor` details.

   ![2048 resolution](/images/tutorial/etl-tutorial/sensor-evaluation.png)

6. Add `request.json` from the `sample_request` folder to `requests` folder

7. Click on the green tick to see the run for this request. 

   ![2048 resolution](/images/tutorial/etl-tutorial/sensor-asset-run.png)


## Next Steps

Now that we have our complete project, the next step is to refactor the project into more a more manageable structure so we can add to it as needed. 

Finish the tutorial with [refactoring the project](/tutorial/etl-tutorial/refactoring-the-project)