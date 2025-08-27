---
description: Sensors emit log messages during evaluation, viewable in tick history in the Dagster UI.
sidebar_position: 200
title: Logging in sensors
---

import ScaffoldSensor from '@site/docs/partials/\_ScaffoldSensor.md';

<ScaffoldSensor />

Any sensor can emit log messages during its evaluation function:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/sensors/sensors.py"
  startAfter="start_sensor_logging"
  endBefore="end_sensor_logging"
  title="src/<project_name>/defs/sensors.py"
/>

These logs can be viewed when inspecting a tick in the tick history view on the corresponding sensor page.

:::note

Sensor logs are stored in your Dagster instance's compute log storage. You should ensure that your compute log storage is configured to view your sensor logs. For more information, see "[Dagster instance configuration](/deployment/oss/oss-instance-configuration#compute-log-storage)".

:::
