---
title: Automation
description: Automating our pipeline
sidebar_position: 80
---

There are several ways to [automate assets](/guides/automate) in Dagster. Dagster supports both scheduled and event-driven pipelines. In this step, you will add a [schedule](/guides/automate/schedules) object to automate the assets you have created.

Similar to resources, schedules exist within the `Definitions` layer.

![2048 resolution](/images/tutorial/dagster-tutorial/overviews/schedules.png)

## 1. Scaffold a schedule definition

Cron-based schedules are common in data orchestration. They use time-based expressions to automatically trigger tasks at specified intervals, making them ideal for ETL pipelines that need to run consistently—such as hourly, daily, or monthly—to process and update data on a regular cadence. For the tutorial pipeline, you can assume that updated CSVs are uploaded at a specific time every day.

Use the `dg scaffold defs` command to scaffold a new schedule object:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/dagster-tutorial/commands/dg-scaffold-schedules.txt" />

This will add a generic schedules file to your project. The `schedules.py` file is now part of the `dagster-tutorial` module:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/dagster-tutorial/tree/schedules.txt" />

There is very little you need to change about the schedule that has been scaffolded. Schedules consist of a `cron_schedule` and `target`. By default the `cron_schedule` will be set to `@daily` and the `target` will be set to `*`. You can keep the `target` as is, but change the `cron_schedule` to something more specific. The code below updates the [cron syntax](https://crontab.guru/) to run at midnight, and updates the schedule name by renaming the function to `tutorial_schedule`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/dagster-tutorial/src/dagster_tutorial/defs/schedules.py"
  language="python"
  title="src/dagster_tutorial/defs/schedules.py"
/>

## 2. Enable automation

To enable automation:

1. Run `dg dev` (if it is not already running) and navigate to the Dagster UI at [http://127.0.0.1:3000](http://127.0.0.1:3000).
2. Navigate to **Assets**.
3. Click **Reload definitions**.
4. Click **Automation**.

   ![2048 resolution](/images/tutorial/dagster-tutorial/automation-1.png)

5. View your automation events to see if anything is ready to run.

   ![2048 resolution](/images/tutorial/dagster-tutorial/automation-2.png)
