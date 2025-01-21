---
title: Logging in sensors
sidebar_position: 200
---

Any sensor can emit log messages during its evaluation function:

{/* TODO convert to <CodeExample> */}
```python file=concepts/partitions_schedules_sensors/sensors/sensors.py startafter=start_sensor_logging endbefore=end_sensor_logging
@sensor(target=the_job)
def logs_then_skips(context):
    context.log.info("Logging from a sensor!")
    return SkipReason("Nothing to do")
```

These logs can be viewed when inspecting a tick in the tick history view on the corresponding sensor page.

:::note

Sensor logs are stored in your Dagster instance's compute log storage. You should ensure that your compute log storage is configured to view your sensor logs. For more information, see "[Dagster instance configuration](/guides/deploy/dagster-instance-configuration#compute-log-storage)".

:::
