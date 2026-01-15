---
description: Sensors enable you to take action in response to events that occur either internally within Dagster or in external systems by checking for events at regular intervals and either performing an action or providing an explanation for why the action was skipped.
sidebar_position: 30
title: Sensors
canonicalUrl: '/guides/automate/sensors'
slug: '/guides/automate/sensors'
---

Sensors enable you to take action in response to events that occur either internally within Dagster or in external systems. They check for events at regular intervals and either perform an action or provide an explanation for why the action was skipped.

Examples of events include:

- a run completes in Dagster
- a run fails in Dagster
- a job materializes a specific asset
- a file appears in an s3 bucket
- an external system is down

Examples of actions include:

- launching a run
- sending a Slack message
- inserting a row into a database

:::tip

An alternative to polling with sensors is to push events to Dagster using the [Dagster GraphQL API](/api/graphql).

:::

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Familiarity with [assets](/guides/build/assets)
- Familiarity with [jobs](/guides/build/jobs)

</details>

## Basic sensor

Sensors are defined with the `@sensor` decorator. The following example includes a `check_for_new_files` function that simulates finding new files. In a real scenario, this function would check an actual system or directory.

:::tip

You can scaffold assets and sensors from the command line with the `dg scaffold` command. For more information, see the [`dg` CLI docs](/api/clis/dg-cli/dg-cli-reference#dg-scaffold).

:::

If the sensor finds new files, it starts a run of `my_job`. If not, it skips the run and logs `No new files found` in the Dagster UI.

<CodeExample
  path="docs_snippets/docs_snippets/guides/automation/simple-sensor-example.py"
  language="python"
  title="src/<project_name>/defs/assets.py"
/>

:::tip
Unless a sensor has a `default_status` of `DefaultSensorStatus.RUNNING`, it won't be enabled when first deployed to a Dagster instance. To find and enable the sensor, click **Automation > Sensors** in the Dagster UI.

To explicitly disable a sensor, you can use `DefaultSensorStatus.STOPPED`.
:::

## Customizing intervals between evaluations

The `minimum_interval_seconds` argument allows you to specify the minimum number of seconds that will elapse between sensor evaluations. This means that the sensor won't be evaluated more frequently than the specified interval.

It's important to note that this interval represents a minimum interval between runs of the sensor and not the exact frequency the sensor runs. If a sensor takes longer to complete than the specified interval, the next evaluation will be delayed accordingly.

```python
# Sensor will be evaluated at least every 30 seconds
@dg.sensor(job=my_job, minimum_interval_seconds=30)
def new_file_sensor():
  ...
```

In this example, if the `new_file_sensor`'s evaluation function takes less than a second to run, you can expect the sensor to run consistently around every 30 seconds. However, if the evaluation function takes longer, the interval between evaluations will be longer.

## Preventing duplicate runs

To prevent duplicate runs, you can use run keys to uniquely identify each `RunRequest`. In the [previous example](#basic-sensor), the `RunRequest` was constructed with a `run_key`:

```
yield dg.RunRequest(run_key=filename)
```

For a given sensor, a single run is created for each `RunRequest` with a unique `run_key`. Dagster will skip processing requests with previously used run keys, ensuring that duplicate runs won't be created.

## Cursors and high volume events

When dealing with a large number of events, you may want to implement a cursor to optimize sensor performance. Unlike run keys, cursors allow you to implement custom logic that manages state.

The following example demonstrates how you might use a cursor to only create `RunRequests` for files in a directory that have been updated since the last time the sensor ran.

<CodeExample
  path="docs_snippets/docs_snippets/guides/automation/sensor-cursor.py"
  language="python"
  title="src/<project_name>/defs/assets.py"
/>

For sensors that consume multiple event streams, you may need to serialize and deserialize a more complex data structure in and out of the cursor string to keep track of the sensor's progress over the multiple streams.

:::note
The preceding example uses both a `run_key` and a cursor, which means that if the cursor is reset but the files don't change, new runs won't be launched. This is because the run keys associated with the files won't change.

If you want to be able to reset a sensor's cursor, don't set `run_key`s on `RunRequest`s.
:::

## Accessing tags from upstream job runs

When working with sensors in Dagster, you might need to access tags from upstream job runs. For example, you may want to retrieve the partition key from an upstream job's tags to trigger downstream jobs with specific partition keys:

```python
from dagster import sensor, AssetKey, RunRequest

@sensor(asset_key=AssetKey("my_asset"))
def my_asset_sensor(context, asset_event):
    # Retrieve the partition key from the upstream job's tags
    partition_key = asset_event.dagster_event.logging_tags.get("dagster/partition")

    if partition_key:
        # Trigger the downstream job with the partition key
        return RunRequest(
            run_key=partition_key,
            tags={"dagster/partition": partition_key},
        )
    return None
```

## Next steps

By understanding and effectively using these automation methods, you can build more efficient data pipelines that respond to your specific needs and constraints.

- Run pipelines on a [schedule](/guides/automate/schedules)
- Trigger cross-job dependencies with [asset sensors](/guides/automate/asset-sensors)
- Explore [Declarative Automation](/guides/automate/declarative-automation) as an alternative to sensors
