---
title: Automate your pipeline
description: Set schedules and utilize asset based automation
last_update:
  author: Alex Noonan
sidebar_position: 60
---

There are several ways to automate pipelines and assets [in Dagster](/guides/automate). 

In this step you will:

- Add automation to assets to run when upstream assets are materialized.
- Create a schedule to run a set of assets on a cron schedule.

## 1. Automate asset materialization 

Ideally, the reporting assets created in the last step should refresh whenever the upstream data is updated. Dagster's [declarative automation](/guides/automate/declarative-automation) framework allows you do this by adding an automation condition to the asset definition.

Update the `monthly_sales_performance` asset to add the automation condition to the decorator:

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="155" lineEnd="209"/>

Do the same thing for `product_performance`:

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="216" lineEnd="267"/>

## 2. Scheduled jobs

Cron-based schedules are common in data orchestration. For our pipeline, assume that updated CSVs are uploaded to a file location at a specific time every week by an external process.

Copy the following code underneath the `product performance` asset:

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="268" lineEnd="273"/>

## 3. Enable and test automations

The final step is to enable the automations in the UI.

To accomplish this:
1. Navigate to the Automation page.
2. Select all automations. 
3. Using actions, start all automations. 
4. Select the `analysis_update_job`.
5. Test the schedule and evaluate for any time in the dropdown menu. 
6. Open in Launchpad.

The job is now executing. 

Additionally, if you navigate to the Runs tab, you should see that materializations for `monthly_sales_performance` and `product_performance` have run as well. 

   ![2048 resolution](/images/tutorial/etl-tutorial/automation-final.png)

## Next steps

- Continue this tutorial with adding a [sensor based asset](create-a-sensor-asset)