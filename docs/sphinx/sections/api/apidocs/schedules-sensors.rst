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
     :members: evaluate_tick

.. autoclass:: ScheduleExecutionContext
.. autoclass:: PartitionScheduleDefinition

.. autofunction:: build_schedule_context

.. currentmodule:: dagster.core.scheduler

.. autoclass:: DagsterDaemonScheduler

Sensors
=======

.. currentmodule:: dagster

.. autodecorator:: sensor

.. autoclass:: SensorDefinition
     :members: evaluate_tick

.. autoclass:: SensorExecutionContext

.. autofunction:: build_sensor_context
