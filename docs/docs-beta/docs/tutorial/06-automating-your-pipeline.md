---
title: Automating your pipeline
description: Set schedules and utilize asset based automation
last_update:
  author: Alex Noonan
---

# Automation

There are several ways to automate pipelines and assets [in Dagster](guides/automation). 

In this step you will:

- Add automation to assets to run when upstream assets are materialized
- Create a schedule to run a set of assets on a cron schedule

## 1. Automating asset materialization 

The reporting assets created in the last step should refresh whenever the upstream data is updated. To accomplish this we will add an eager automation condition to asset definition. 

Update the `monthly_sales_performance` asset to have the automation condition in the decorator:

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="155" lineEnd="209"/>

Do the same thing for `product_performance`:

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="217" lineEnd="267"/>

## 2. Scheduled Jobs

CRON based schedules are a common use case in data orchestration. In this scenario, we need a job to update the source files on a weekly basis. Since we already defined the performance assets to materialize when the upstream data is updated the entire pipeline will refresh. 

Copy the following code underneath the `product performance` asset:

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="267" lineEnd="273"/>

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

Additionally if you navigaet to the runs tab you will see that materializations for `monthly_sales_performance` and `product_performance` have ran as well. 

   ![2048 resolution](/images/tutorial/etl-tutorial/automation-final.png)

## Next steps

- Continue this tutorial with adding a [sensor based asset](/tutorial/07-creating-a-sensor-asset)