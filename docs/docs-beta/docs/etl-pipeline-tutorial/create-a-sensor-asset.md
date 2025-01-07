---
title: Create a sensor asset
description: Use sensors to create event driven pipelines
last_update:
  author: Alex Noonan
sidebar_position: 70
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

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="275" lineEnd="312"/>

## 2. Build the sensor

To define a sensor in Dagster, use the `@sensor` decorator. This decorator is applied to a function that evaluates whether the conditions for triggering a job are met.

Sensors include the following elements:

- **Job**: The job that the sensor will trigger when the conditions are met.
- **RunRequest**: An object that specifies the configuration for the job run. It includes a `run_key` to ensure idempotency and a `run_config` for job-specific settings.

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="314" lineEnd="355"/>

## 3. Materialize the sensor asset

1. Update your Definitions object to the following:

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="357" lineEnd="373"/>

2. Reload your Definitions.

3. Navigate to the Automation page.

4. Turn on the `automation_request_sensor`.

5. Click on the `automation_request_sensor` details.

   ![2048 resolution](/images/tutorial/etl-tutorial/sensor-evaluation.png)

6. Add `request.json` from the `sample_request` folder to `requests` folder.

7. Click on the green tick to see the run for this request. 

   ![2048 resolution](/images/tutorial/etl-tutorial/sensor-asset-run.png)


## Next steps

Now that we have our complete project, the next step is to refactor the project into more a more manageable structure so we can add to it as needed. 

Finish the tutorial by [refactoring your project](refactor-your-project).