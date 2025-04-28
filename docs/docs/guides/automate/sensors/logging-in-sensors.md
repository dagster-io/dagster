---
title: Logging in sensors
sidebar_position: 200
---

Any sensor can emit log messages during its evaluation function:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/sensors/sensors.py"
  startAfter="start_sensor_logging"
  endBefore="end_sensor_logging"
/>

These logs can be viewed when inspecting a tick in the tick history view on the corresponding sensor page.

:::note

Sensor logs are stored in your Dagster instance's compute log storage. You should ensure that your compute log storage is configured to view your sensor logs. For more information, see "[Dagster instance configuration](/guides/deploy/dagster-instance-configuration#compute-log-storage)".

:::
