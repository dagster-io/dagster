---
title: Automation
description: Automating our pipeline
sidebar_position: 80
---

There are several ways to [automate assets](/guides/automate) in Dagster. Dagster supports both scheduled and event-driven pipelines. In this step, we will add a [schedule](/guides/automate/schedules) object in Dagster to automate the assets we have created.

Similar to resources, schedules exist within the `Definitions` layer though they are not directly executed as `Ops`.

![2048 resolution](/images/tutorial/dagster-tutorial/overviews/schedules.png)

## 1. Scheduled assets

Cron-based schedules are common in data orchestration. They use time-based expressions to automatically trigger tasks at specified intervals, making them ideal for ETL pipelines that need to run consistently—such as hourly, daily, or monthly—to process and update data on a regular cadence. For our pipeline, assume that updated CSVs are uploaded at a specific time every day.

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/dagster-tutorial/commands/dg-scaffold-schedules.txt" />

This adds a generic schedules file to our project. The `schedules.py` file is now part of the `dagster-tutorial` module:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/dagster-tutorial/tree/schedules.txt" />

There is very little we need to change about the schedule that has been scaffolded. Schedules consist of a `cron_schedule` and `target`. By default the `cron_schedule` will be set to `@daily` and the `target` will be set to `*`. We can keep the `target` as is but we can change the `cron_schedule` to something more specific. We update the c[ron syntax](https://crontab.guru/) to run at midnight and update the schedule name by renaming the function to `tutorial_schedule`

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/dagster-tutorial/src/dagster_tutorial/defs/schedules.py"
  language="python"
  title="src/dagster_tutorial/defs/schedules.py"
/>

## 2. Enable automation

Run `dg dev` (if it is not already running) and go to the Dagster UI at [http://127.0.0.1:3000](http://127.0.0.1:3000). You can now enable the automation condition:

1. Reload your Definitions.
2. Click **Automation**.
3. Enable the `default_automation_condition_sensor`.

   ![2048 resolution](/images/tutorial/dagster-tutorial/automation-1.png)

4. View your automation events to see if anything is ready to run.

   ![2048 resolution](/images/tutorial/dagster-tutorial/automation-2.png)
