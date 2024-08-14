---
title: "Automating Pipelines"
description: Learn how to automate your data pipelines.
last_update: 
    date: 2024-08-12
    author: Pedram Navid
---

# How To Automate Pipelines in Dagster

Automation is key to building reliable, efficient data pipelines. 
This guide provides a simplified overview of the main ways to automate processes in Dagster, 
helping you choose the right method for your needs. You will find links to more detailed guides for each method below.

## What You'll Learn

- The different automation options available in Dagster
- How to implement basic scheduling and event-based triggers  
- Best practices for selecting and using automation methods

<details>
  <summary>Prerequisites</summary>

Before continuing, you should be familiar with:

- [Asset definitions](/concepts/assets)
- [Jobs](/concepts/ops-jobs)

</details>

## Automation Methods Overview

Dagster offers several ways to automate pipeline execution:

1. [Schedules](#schedules) - Run jobs at specified times
2. [Sensors](#sensors) - Trigger runs based on events
3. [Asset Sensors](#asset-sensors) - Trigger jobs when specific assets materialize

Let's look at each method in more detail.

## Schedules 

Schedules allow you to run jobs at specified times, like "every Monday at 9 AM" or "daily at midnight."
A schedule combines a selection of assets, known as a [Job](/concepts/jobs), and a [cron expression](https://en.wikipedia.org/wiki/Cron) 
in order to define when the job should be run.

To make creating cron expressions easier, you can use an online tool like [Crontab Guru](https://crontab.guru/).

### When to use Schedules

- You need to run jobs at regular intervals
- You want basic time-based automation

### Basic Schedule Example

<CodeExample filePath="guides/automation/simple-schedule-example.py" language="python" title="Simple Schedule Example" />

For more examples of schedules, see the [How-To Use Schedules](/guides/automation/schedules) guide.

For more information about how Schedules work, see the [About Schedules](/concepts/schedules) concept page.

## Sensors

Sensors allow you to trigger runs based on events or conditions, like a new file arriving or an external system status change.

Like schedules, sensors operate on a selection of assets, known as [Jobs](/concepts/jobs) and can either start a pipeline 
through a [Run](/concepts/runs) or log a reason for not starting a pipeline using a [SkipReason](/concepts/sensors#skip-reasons).

However, unlike schedules, sensors are triggered by events that you define.
You must provide a function that the sensor will use to determine if it should trigger a run.

### When to use Sensors

- You need event-driven automation
- You want to react to changes in external systems

### Basic Sensor Example 

This example includes a `check_for_new_files` function that simulates finding new files. In a real scenario, this function would check an actual system or directory.

The sensor runs every 5 seconds. If it finds new files, it starts a run of `my_job`. If not, it skips the run and logs "No new files found" in the Dagster UI.

<CodeExample filePath="guides/automation/simple-sensor-example.py" language="python" title="Simple Sensor Example" />

:::tip

By default, sensors aren't enabled when first deployed to a Dagster instance.
Click "Automation" in the top navigation to find and enable a sensor.

:::

## Asset Sensors

Asset Sensors trigger jobs when specified assets are materialized, allowing you to create dependencies between jobs or code locations.

### When to use Asset Sensors

- You need to trigger jobs based on asset materializations
- You want to create dependencies between different jobs or code locations

### Basic Asset Sensor Example

<CodeExample filePath="guides/automation/simple-asset-sensor-example.py" language="python" title="Simple Asset Sensor Example" />

This Asset Sensor will trigger a run of `my_job` whenever the `asset_to_watch` asset is materialized.

## Choosing the Right Automation Method

Consider these factors when selecting an automation method:

1. **Pipeline Structure**: Are you working primarily with assets, ops, or a mix?
2. **Timing Requirements**: Do you need regular updates or event-driven processing?
3. **Data Characteristics**: Is your data partitioned? Do you need to update historical data?
4. **System Integration**: Do you need to react to external events or systems?

Use this table to help guide your decision:

| Method | Best For | Works With |
|--------|----------|------------|
| Schedules | Regular, time-based job runs | Assets, Ops, Graphs |
| Sensors | Event-driven automation | Assets, Ops, Graphs |
| Declarative Automation | Asset-centric, condition-based updates | Assets only |
| Asset Sensors | Cross-job/location asset dependencies | Assets only |

## Next Steps

- Learn more about [advanced scheduling patterns] - TODO ADD LINK
- Explore [complex sensor examples] - TODO ADD LINK
- Dive into [Declarative Automation best practices] - TODO ADD LINK

By understanding and effectively using these automation methods, you can build more efficient data pipelines that respond to your specific needs and constraints.