---
title: Automate your pipeline
description: Set schedules and utilize asset based automation
last_update:
  author: Alex Noonan
sidebar_position: 50
---

There are several ways to automate pipelines and assets [in Dagster](/guides/automate). 

In this step you will:

- Add automation to assets to run when upstream assets are materialized.
- Create a schedule to run a set of assets on a cron schedule.

## 1. Scheduled jobs

Cron-based schedules are common in data orchestration. For our pipeline, assume that updated CSVs are uploaded to a file location at a specific time every week by an external process.

Copy the following code underneath the `product performance` asset:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="268" lineEnd="273"/>

## 2. Automate asset materialization 

Now, `monthly_sales_performance` should be executed once a month, but setting up an independent monthly schedule for this asset isn't exactly what we want -- if we do it naively, then this asset will execute exactly on the month boundary before the last week's data has had a chance to complete. We could delay the monthly schedule by a couple of hours to give the upstream assets a chance to finish, but what if the upstream computation fails or takes too long to complete? This is where we can use [declarative automation](/guides/automate/declarative-automation), which understands the status of an asset and all of its dependencies. 

For `monthly_sales_performance`, we want it to update when all the dependencies are updated. To accomplish this, we will use the `eager` automation condition. Update the `monthly_sales_performance` asset to add the automation condition to the decorator:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="155" lineEnd="209"/>

Do the same thing for `product_performance`:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="216" lineEnd="267"/>



## 3. Enable and test automations

Now that we have our schedule, let's add it to our Definitions object.

Your Definitions object should look like this:

  ```python
  defs = dg.Definitions(
      assets=[products,
          sales_reps,
          sales_data,
          joined_data,
          monthly_sales_performance,
          product_performance,
      ],
      asset_checks=[missing_dimension_check],
      schedules=[weekly_update_schedule],
      resources={"duckdb": DuckDBResource(database="data/mydb.duckdb")},
  )
  ```

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
