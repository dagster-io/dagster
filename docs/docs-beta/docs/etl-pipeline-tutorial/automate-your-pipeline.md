---
title: Automate your pipeline
description: Set schedules and utilize asset based automation
last_update:
  author: Alex Noonan
sidebar_position: 60
---

There are several ways to automate pipelines and assets [in Dagster](/guides/automate). 

In this step you will:

- Add automation to assets to run when upstream assets are materialized
- Create a schedule to run a set of assets on a cron schedule

## 1. Automating asset materialization 

Ideally, the reporting assets created in the last step should refresh whenever the upstream data is updated. This can be done simply using [declarative automation](/guides/automate/declarative-automation) and adding an automation condition to the asset definition.

Update the `monthly_sales_performance` asset to have the automation condition in the decorator:

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="155" lineEnd="209"/>

Do the same thing for `product_performance`:

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="216" lineEnd="267"/>

## 2. Scheduled Jobs

CRON based schedules are common in data orchestration. For our pipeline, assume updated csv's get dropped into a file location every week at a specified time by an external process. We want to have a job that runs the pipeline and materialize the asset. Since we already defined the performance assets to materialize using the eager condition, When the upstream data is updated the entire pipeline will refresh. 

Copy the following code underneath the `product performance` asset:

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="268" lineEnd="273"/>

## 3. Running the entire pipeline

With automation in Dagster the final step is to turn on the automations in the UI. 

To accomplish this:
1. Navigate to the Automation page.
2. Select all the automations. 
3. Using actions, start all automations. 
4. Select the `analysis_update_job`
5. Test Schedule and evaluate for any time in the drop down. 
6. Open in Launchpad

The job is now executing. 

Additionally if you navigate to the runs tab you will see that materializations for `monthly_sales_performance` and `product_performance` have ran as well. 

   ![2048 resolution](/images/tutorial/etl-tutorial/automation-final.png)

## Next steps

- Continue this tutorial with adding a [sensor based asset](/tutorial/creating-a-sensor-asset)