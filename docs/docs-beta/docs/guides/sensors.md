---
title: Creating event-based pipelines with sensors
sidebar_label: Event triggers
sidebar_position: 20
---

Sensors enable you to trigger Dagster runs in response to events from external systems. They run at regular intervals, either triggering a run or explaining why a run was skipped. For example, you can trigger a run when a new file is added to an Amazon S3 bucket or when a database row is updated.

<details>
<summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Familiarity with [Assets](/concepts/assets)
- Familiarity with [Ops and Jobs](/concepts/ops-jobs)
</details>

## Basic sensor

Sensors are defined with the `@sensor` decorator. The following example includes a `check_for_new_files` function that simulates finding new files. In a real scenario, this function would check an actual system or directory.

If the sensor finds new files, it starts a run of `my_job`. If not, it skips the run and logs `No new files found` in the Dagster UI.

<CodeExample filePath="guides/automation/simple-sensor-example.py" language="python" />

:::tip
Unless a sensor has a `default_status` of `DefaultSensorStatus.RUNNING`, it won't be enabled when first deployed to a Dagster instance. To find and enable the sensor, click **Automation > Sensors** in the Dagster UI.
:::

By default, sensors aren't enabled when first deployed to a Dagster instance.
Click "Automation" in the top navigation to find and enable a sensor.

:::
