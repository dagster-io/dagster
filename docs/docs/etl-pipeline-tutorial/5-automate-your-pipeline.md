---
title: Automate your pipeline
description: Set schedules and utilize asset based automation
sidebar_position: 60
---

There are several ways to automate assets [in Dagster](/guides/automate). In this step you will:

- Add automation to assets to run when upstream assets are materialized.

## 1. Scheduled assets

Cron-based schedules are common in data orchestration. For our pipeline, assume that updated CSVs are uploaded to a file location at a specific time every day by an external process.

With [declarative automation](/guides/automate/declarative-automation), we can include this schedule information within the `dg.asset` decorator. Now our assets will execute every day at midnight:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/src/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_ingest_assets_3"
  endBefore="end_ingest_assets_3"
  title="src/etl_tutorial/defs/assets.py"
/>

## 2. Other asset automation

Now let's look at `monthly_sales_performance`. This asset should be executed once a month, but setting up an independent monthly schedule for this asset isn't exactly what we want -- if we do it naively, then this asset will execute exactly on the month boundary before the last week's data has had a chance to complete. We could delay the monthly schedule by a couple of hours to give the upstream assets a chance to finish, but what if the upstream computation fails or takes too long to complete?

We already set this in the `monthly_sales_performance` by setting the `automation_condition`. We want it to update when all the dependencies are updated. To accomplish this, we will use the `eager` automation condition:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/src/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_monthly_sales_performance_asset_highlight"
  endBefore="end_monthly_sales_performance_asset_highlight"
  title="src/etl_tutorial/defs/assets.py"
/>

# 3. Enabling automation

With declarative automation set for our assets, we can now enable the automation condition:

1. Reload your Definitions.
2. Click on **Automation**.
3. Enable the "default_automation_condition_sensor".

   ![2048 resolution](/images/tutorial/etl-tutorial/enable-automation.png)

4. You can now view your automation events which will check to determine if anything should be run.

   ![2048 resolution](/images/tutorial/etl-tutorial/automation-status.png)

## Summary

Associating automation directly with assets provides flexibility and allows you to compose complex automation conditions across your data platform.  

## Next steps

In the next step, we [build an Evidence dashboard](/etl-pipeline-tutorial/visualize-data) to enable us to visualize data.
