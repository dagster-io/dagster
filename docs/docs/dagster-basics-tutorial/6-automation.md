---
title: Automation
description: Automating our pipeline
sidebar_position: 70
---

There are several ways to [automate assets](/guides/automate) in Dagster. Dagster supports both scheduled and event-driven pipelines. In this step, we will add a schedule directly to one of our assets and make another asset reactive to upstream changes.

## 1. Scheduled assets

Cron-based schedules are common in data orchestration. They use time-based expressions to automatically trigger tasks at specified intervals, making them ideal for ETL pipelines that need to run consistently—such as hourly, daily, or monthly—to process and update data on a regular cadence. For our pipeline, assume that updated CSVs are uploaded at a specific time every day.

While it is possible to define a standalone [schedule](/guides/automate/schedules) object in Dagster, we can also add a schedule directly to an asset with [declarative automation](/guides/automate/declarative-automation). This is done by including schedule information within the <PyObject section="asset-checks" module="dagster" object="asset_check" decorator />. With this approach, our assets will execute every day at midnight:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/dagster-tutorial/src/dagster_tutorial/defs/assets.py"
  language="python"
  startAfter="start_automation_cron"
  endBefore="end_automation_cron"
  title="src/dagster_tutorial/defs/assets.py"
/>

## 2. Eager asset automation

Now let’s look at `orders_by_month`. This asset should execute once a month, but setting up an independent monthly schedule for it is not ideal. If scheduled naively, it would run exactly on the month boundary—before the last week’s data has been fully processed. We could delay the monthly schedule by a couple of hours to give upstream assets time to finish, but that would not account for cases where upstream computation fails or takes longer than expected.

Instead, as we did for `monthly_sales_performance`, we can set an `automation_condition` so that it updates when all its dependencies are updated. To accomplish this, we will use the `eager` automation condition:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/dagster-tutorial/src/dagster_tutorial/defs/assets.py"
  language="python"
  startAfter="start_automation_eager"
  endBefore="end_automation_eager"
  title="src/dagster_tutorial/defs/assets.py"
/>

This triggers the asset automatically when all of its upstream dependencies have completed.

## 3. Enable automation

Run `dg dev` (if it is not already running) and go to the Dagster UI at [http://127.0.0.1:3000](http://127.0.0.1:3000). You can now enable the automation condition:

1. Reload your Definitions.
2. Click **Automation**.
3. Enable the `default_automation_condition_sensor`.

   #TODO Screenshot

4. View your automation events to see if anything is ready to run.

   #TODO Screenshot