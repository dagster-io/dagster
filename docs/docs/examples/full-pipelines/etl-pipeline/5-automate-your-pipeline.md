---
title: Automate your pipeline
description: Set schedules and utilize asset based automation
sidebar_position: 60
---

There are several ways to [automate assets ](/guides/automate) in Dagster. Dagster supports both scheduled and event-driven pipelines. Here, we will add a schedule directly to one of our assets and make another of our assets reactive to any upstream changes.

## 1. Scheduled assets

Cron-based schedules are common in data orchestration. They use time-based expressions to automatically trigger tasks at specified intervals, making them ideal for ETL pipelines that need to run consistently, such as hourly, daily, or monthly, to process and update data on a regular cadence. For our pipeline, assume that updated CSVs are uploaded at a specific time every day.

While it is possible to define a standalone [schedule](/guides/automate/schedules) object in Dagster, we can also add a schedule directly to the asset with [declarative automation](/guides/automate/declarative-automation) by including this schedule information within the <PyObject section="asset-checks" module="dagster" object="asset_check" decorator />. Now our assets will execute every day at midnight:

<CodeExample
  path="docs_projects/project_etl_tutorial/src/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_ingest_assets_3"
  endBefore="end_ingest_assets_3"
  title="src/etl_tutorial/defs/assets.py"
/>

## 2. Other asset automation

Now let's look at `monthly_sales_performance`. This asset should be executed once a month, but setting up an independent monthly schedule for this asset isn't exactly what we want -- if we do it naively, then this asset will execute exactly on the month boundary before the last week's data has had a chance to complete. We could delay the monthly schedule by a couple of hours to give the upstream assets a chance to finish, but what if the upstream computation fails or takes too long to complete?

We already set this in the `monthly_sales_performance` by setting the `automation_condition`. We want it to update when all the dependencies are updated. To accomplish this, we will use the `eager` automation condition:

<CodeExample
  path="docs_projects/project_etl_tutorial/src/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_monthly_sales_performance_asset_highlight"
  endBefore="end_monthly_sales_performance_asset_highlight"
  title="src/etl_tutorial/defs/assets.py"
/>

This will trigger the asset automatically when its upstream dependencies have completed.

## 3. Enabling automation

Run `dg dev` (if it is not already running) and go to the Dagster UI [http://127.0.0.1:3000](http://127.0.0.1:3000). We can now enable the automation condition:

1. Reload your Definitions.
2. Click on **Automation**.
3. Enable the "default_automation_condition_sensor".

   ![2048 resolution](/images/tutorial/etl-tutorial/enable-automation.png)

4. You can now view your automation events which will check to determine if anything should be run.

   ![2048 resolution](/images/tutorial/etl-tutorial/automation-status.png)

## Summary

Associating automation directly with assets provides flexibility and allows you to compose complex automation conditions across your data platform.

## Next steps

In the next step, we [build an Evidence dashboard](/examples/full-pipelines/etl-pipeline/visualize-data) to enable us to visualize data.
