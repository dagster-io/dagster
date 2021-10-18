.. currentmodule:: dagster

Run Requests
============
.. autoclass:: RunRequest
.. autoclass:: SkipReason

Schedules
=========

.. autodecorator:: schedule
.. autodecorator:: hourly_partitioned_config
.. autodecorator:: daily_partitioned_config
.. autodecorator:: weekly_partitioned_config
.. autodecorator:: monthly_partitioned_config

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

.. autodecorator:: job_failure_sensor

.. autodecorator:: pipeline_failure_sensor

.. autoclass:: JobFailureSensorContext

.. autoclass:: PipelineFailureSensorContext

.. autoclass:: RunStatusSensorDefinition

.. autoclass:: RunStatusSensorContext

.. autodecorator:: run_status_sensor
