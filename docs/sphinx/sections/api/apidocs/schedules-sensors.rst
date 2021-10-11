.. currentmodule:: dagster

Run Requests
============
.. autoclass:: RunRequest
.. autoclass:: SkipReason

Schedules
=========

.. autodecorator:: schedule
.. autodecorator:: monthly_schedule
.. autodecorator:: weekly_schedule
.. autodecorator:: hourly_schedule
.. autodecorator:: daily_schedule

.. autoclass:: ScheduleDefinition

.. autoclass:: ScheduleEvaluationContext
.. autoclass:: PartitionScheduleDefinition

.. autofunction:: build_schedule_context

.. currentmodule:: dagster.core.scheduler

.. autoclass:: DagsterDaemonScheduler

Sensors
=======

.. currentmodule:: dagster

.. autodecorator:: sensor

.. autoclass:: SensorDefinition

.. autoclass:: SensorEvaluationContext

.. autofunction:: build_sensor_context

.. autoclass:: AssetSensorDefinition

.. autodecorator:: asset_sensor

.. autodecorator:: pipeline_failure_sensor

.. autoclass:: PipelineFailureSensorContext

.. autoclass:: RunStatusSensorDefinition

.. autoclass:: RunStatusSensorContext

.. autodecorator:: run_status_sensor
