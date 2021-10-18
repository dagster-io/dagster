.. currentmodule:: dagster

Run Requests
============
.. autoclass:: RunRequest
.. autoclass:: SkipReason

Schedules
=========

.. autodecorator:: schedule

.. autoclass:: ScheduleDefinition

.. autoclass:: ScheduleEvaluationContext

.. autofunction:: build_schedule_context

.. currentmodule:: dagster.core.scheduler

.. autoclass:: DagsterDaemonScheduler

Partitioned Schedules
=====================

.. currentmodule:: dagster

.. autofunction:: build_schedule_from_partitioned_job

.. autoclass:: PartitionScheduleDefinition

.. autodecorator:: hourly_partitioned_config
    :noindex:

.. autodecorator:: daily_partitioned_config
    :noindex:

.. autodecorator:: weekly_partitioned_config
    :noindex:

.. autodecorator:: monthly_partitioned_config
    :noindex:

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
