---
title: Create event-based pipelines with sensors
sidebar_label: Sensors
sidebar_position: 20
---

Sensors are a way to trigger runs in response to events in Dagster. Sensors
run on a regular interval and can either trigger a run, or provide a reason why a run was skipped.

Sensors allow you to respond to events in external systems. For example, you can trigger a run when a new file arrives in an S3 bucket, or when a row is updated in a database.

<details>
<summary>Prerequisites</summary>

- Familiarity with [Assets](/concepts/assets)
- Familiarity with [Ops and Jobs](/concepts/ops-jobs)
</details>

## Basic sensor example

This example includes a `check_for_new_files` function that simulates finding new files. In a real scenario, this function would check an actual system or directory.

The sensor runs every 5 seconds. If it finds new files, it starts a run of `my_job`. If not, it skips the run and logs "No new files found" in the Dagster UI.


<CodeExample filePath="guides/automation/simple-sensor-example.py" language="python" title="Simple Sensor Example" />

:::tip

By default, sensors aren't enabled when first deployed to a Dagster instance.
Click "Automation" in the top navigation to find and enable a sensor.

:::
