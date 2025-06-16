---
title: Automate your pipeline
description: Set schedules and utilize asset based automation
sidebar_position: 70
---

There are several ways to automate pipelines and assets [in Dagster](/guides/automate).

In this step you will:

- Add automation to assets to run when upstream assets are materialized.
- Create a schedule to run a set of assets on a cron schedule.

## 1. Scheduled jobs

Cron-based schedules are common in data orchestration. For our pipeline, assume that updated CSVs are uploaded to a file location at a specific time every week by an external process.

First we will use `dg`, this time for schedules:

```bash
dg scaffold dagster.schedule schedules.py
```

Copy the following code in the `defs/schedules.py` file created by the `dg` command:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial_components/src/etl_tutorial_components/defs/schedules.py"
  language="python"
  title="src/etl_tutorial_components/defs/schedules.py"
/>

## 2. Automate asset materialization

Now, `monthly_sales_performance` should be executed once a month, but setting up an independent monthly schedule for this asset isn't exactly what we want -- if we do it naively, then this asset will execute exactly on the month boundary before the last week's data has had a chance to complete. We could delay the monthly schedule by a couple of hours to give the upstream assets a chance to finish, but what if the upstream computation fails or takes too long to complete?

This is where we can use [declarative automation](/guides/automate/declarative-automation), which understands the status of an asset and all of its dependencies.

We already set this in the `monthly_sales_performance` and `product_performance` by setting the `automation_condition`. We want it to update when all the dependencies are updated. To accomplish this, we will use the `eager` automation condition.

## 3. Enable and test automations

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

- Continue this tutorial with adding a [sensor based asset](/etl-pipeline-tutorial/create-a-sensor-asset)
