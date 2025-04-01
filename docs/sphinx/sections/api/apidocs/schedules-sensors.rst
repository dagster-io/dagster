.. currentmodule:: dagster

Schedules and sensors
=====================

Dagster offers several ways to run data pipelines without manual intervation, including traditional scheduling and event-based triggers. `Automating your Dagster pipelines <https://docs.dagster.io/guides/automate/>`_ can boost efficiency and ensure that data is produced consistently and reliably.

----

Run requests
------------
.. autoclass:: RunRequest
.. autoclass:: SkipReason

----

Schedules
---------

`Schedules <https://docs.dagster.io/guides/automate/schedules/>`__ are Dagster's way to support traditional ways of automation, such as specifying a job should run at Mondays at 9:00AM. Jobs triggered by schedules can contain a subset of `assets <https://docs.dagster.io/guides/build/assets/>`__ or `ops <https://legacy-docs.dagster.io/concepts/ops-jobs-graphs/ops>`__.

.. autodecorator:: schedule

.. autoclass:: ScheduleDefinition

.. autoclass:: ScheduleEvaluationContext

.. autofunction:: build_schedule_context

.. autofunction:: build_schedule_from_partitioned_job

.. currentmodule:: dagster._core.scheduler

.. autoconfigurable:: DagsterDaemonScheduler
  :annotation: Scheduler

----

Sensors
-------

`Sensors <https://docs.dagster.io/guides/automate/sensors/>`_ are typically used to poll, listen, and respond to external events. For example, you could configure a sensor to run a job or materialize an asset in response to specific events.

.. currentmodule:: dagster

.. autodecorator:: sensor

.. autoclass:: SensorDefinition

.. autoclass:: SensorEvaluationContext
   :noindex:

.. autofunction:: build_sensor_context

.. autodecorator:: asset_sensor

.. autodecorator:: multi_asset_sensor

.. autodecorator:: run_status_sensor

.. autodecorator:: run_failure_sensor

.. autoclass:: AssetSensorDefinition

.. autoclass:: MultiAssetSensorDefinition

.. autoclass:: RunStatusSensorDefinition

.. autoclass:: RunStatusSensorContext

.. autoclass:: RunFailureSensorContext

.. autoclass:: JobSelector

.. autoclass:: RepositorySelector

.. autofunction:: build_run_status_sensor_context

.. autoclass:: SensorResult

.. autoclass:: AddDynamicPartitionsRequest

.. autoclass:: DeleteDynamicPartitionsRequest