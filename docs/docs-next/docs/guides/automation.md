---
title: "Automating Pipelines"
description: Learn how to automate your data pipelines.
last_update: 
    date: 2024-08-12
    author: Pedram Navid
---

# How To Automate Pipelines in Dagster

Automation is key to building reliable, efficient data pipelines. This guide covers the main ways to automate processes in Dagster, helping you choose the right method for your needs.

## What You'll Learn

- The different automation options available in Dagster
- How to implement basic scheduling and event-based triggers  
- Best practices for selecting and using automation methods

<details>
  <summary>Prerequisites</summary>

Before continuing, you should be familiar with:

- [Asset definitions](concepts/assets)
- [Jobs](concepts/jobs)

</details>

## Automation Methods Overview

Dagster offers several ways to automate pipeline execution:

1. Schedules - Run jobs at specified times
2. Sensors - Trigger runs based on events
3. Declarative Automation - Automatically materialize assets based on conditions  
4. Asset Sensors - Trigger jobs when specific assets materialize

Let's look at each method in more detail.

## Schedules 

Schedules allow you to run jobs at specified times, like "every Monday at 9 AM" or "daily at midnight."
A schedule combines a selection of assets, known as a [Job](/concepts/jobs), and a cron expression in order to define when the job should be run.
To make creating cron expressions easier, you can use an online tool like [Crontab Guru](https://crontab.guru/).

### When to use Schedules

- You need to run jobs at regular intervals
- You want a basic time-based automation method

### Basic Schedule Example

```python
from dagster import ScheduleDefinition, define_asset_job

# A job is a selection of assets that are grouped together for execution
daily_refresh_job = define_asset_job("daily_refresh", selection=["customer_data", "sales_report"])

# Create a schedule that runs the job daily at midnight
daily_schedule = ScheduleDefinition(
    job=daily_refresh_job,
    cron_schedule="0 0 * * *"  # Runs at midnight daily
)
```

View more detailed examples of schedules in the [How-To Use Schedules](/guides/automation/schedules) 
and read more about how Schedules work in [About Schedules](/concepts/schedules).

## Sensors

Sensors allow you to trigger runs based on events or conditions, like a new file arriving or an external system status change.

A sensor requires that you define a function that will 

### When to use Sensors

- You need event-driven automation
- You want to react to changes in external systems

### Basic Sensor Example 

```python
from dagster import RunRequest, SensorDefinition, sensor

@asset
def my_asset():
    ...

my_job = define_asset_job("my_job", selection=[my_asset])

def check_for_new_files() -> List[str]:
    return ["file1", "file2"]

@sensor(job=my_job)
def new_file_sensor():
    new_files = check_for_new_files()
    if new_files:
        yield RunRequest(run_key=f"filename")

```

## 3. Declarative Automation

Declarative Automation allows you to automatically materialize assets when specified criteria are met, without needing to define explicit jobs.

### When to use Declarative Automation

- You're working primarily with assets
- You want a simpler, more declarative approach to automation

### Basic Declarative Automation Example

```python
from dagster import asset, AutoMaterializePolicy, AutoMaterializeRule

@asset(
    auto_materialize_policy=AutoMaterializePolicy(
        rules=[
            # Materialize if upstream assets have changed
            AutoMaterializeRule.materialize_on_parent_updated(),
            # Materialize daily at 2 AM
            AutoMaterializeRule.materialize_on_cron("0 2 * * *"),
        ]
    )
)
def my_asset():
    # Asset computation logic here
    pass
```

## 4. Asset Sensors

Asset Sensors trigger jobs when specified assets are materialized, allowing you to create dependencies between jobs or code locations.

### When to use Asset Sensors

- You need to trigger jobs based on asset materializations
- You want to create dependencies between different jobs or code locations

### Basic Asset Sensor Example

```python
from dagster import AssetSensor, RunRequest, asset_sensor

@asset_sensor(asset_key=["raw_data"], job=process_raw_data_job)
def raw_data_sensor(context):
    yield RunRequest(run_key=context.cursor)
```

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

- Learn more about [advanced scheduling patterns](link-to-advanced-scheduling)
- Explore [complex sensor examples](link-to-sensor-examples)
- Dive into [Declarative Automation best practices](link-to-declarative-automation)

By understanding and effectively using these automation methods, you can build robust, efficient data pipelines that respond to your specific needs and constraints.