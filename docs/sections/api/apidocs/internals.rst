Internals
=========

.. currentmodule:: dagster

Please note that internal APIs are likely to be in much greater flux pre-1.0 than user-facing APIs,
particularly if not exported in the top level ``dagster`` module.

If you find yourself consulting these docs because you are writing custom components and plug-ins,
please get in touch with the core team `on our Slack <https://join.slack.com/t/dagster/shared_invite/enQtNjEyNjkzNTA2OTkzLTI0MzdlNjU0ODVhZjQyOTMyMGM1ZDUwZDQ1YjJmYjI3YzExZGViMDI1ZDlkNTY5OThmYWVlOWM1MWVjN2I3NjU>`_.
We're curious what you're up to, happy to help, excited for new community contributions, and eager
to make the system as easy to work with as possible -- including for teams who are looking to
customize it.

Logging
-------

.. autoclass:: DagsterLogManager
    :members:

----

Executors
---------
.. autodecorator:: executor

.. autoclass:: ExecutorDefinition

.. autoclass:: InitExecutorContext
    :members:

.. autoclass:: ExecutorConfig
    :members:

.. autoclass:: Engine
    :members:

----

System Storage
--------------
.. autodecorator:: system_storage

.. autoclass:: SystemStorageDefinition

.. currentmodule:: dagster.core.storage.system_storage

----

Instance
--------

.. currentmodule:: dagster.core.instance

.. autoclass:: DagsterInstance
   :members:

.. autoclass:: InstanceRef
   :members:

.. currentmodule:: dagster.core.serdes

.. autoclass:: ConfigurableClass
   :members:

.. autoclass:: ConfigurableClassData
   :members:

.. currentmodule:: dagster.core.storage.root

.. autoclass:: LocalArtifactStorage
   :properties:

Run storage
-----------

.. currentmodule:: dagster.core.storage.runs

.. autoclass:: RunStorage

.. autoclass:: SqlRunStorage

.. autoclass:: SqliteRunStorage

.. currentmodule:: dagster_postgres.run_storage

.. autoclass:: PostgresRunStorage

.. currentmodule:: dagster.core.storage.pipeline_run

.. autoclass:: PipelineRun

Event log storage
-----------------

.. currentmodule:: dagster.core.storage.event_log

.. autoclass:: EventLogStorage

.. autoclass:: SqlEventLogStorage

.. autoclass:: SqliteEventLogStorage

.. currentmodule:: dagster_postgres.event_log

.. autoclass:: PostgresEventLogStorage


Compute log manager
-------------------

.. currentmodule:: dagster.core.storage.compute_log_manager

.. autoclass:: ComputeLogManager

.. currentmodule:: dagster.core.storage.local_compute_log_manager

.. autoclass:: LocalComputeLogManager


.. currentmodule:: dagster_aws.s3.compute_log_manager

.. autoclass:: S3ComputeLogManager

Run launcher
------------
.. currentmodule:: dagster.core.launcher

.. autoclass:: RunLauncher

.. currentmodule:: dagster_graphql.launcher

.. autoclass:: RemoteDagitRunLauncher

.. currentmodule:: dagster_k8s.launcher

.. autoclass:: K8sRunLauncher


Scheduling
----------

.. currentmodule:: dagster.core.scheduler

.. autoclass:: Scheduler


.. currentmodule:: dagster_cron.cron_scheduler

.. autoclass:: SystemCronScheduler


.. currentmodule:: dagster.core.storage.schedules

.. autoclass:: ScheduleStorage

.. autoclass:: SqlScheduleStorage

.. autoclass:: SqliteScheduleStorage


.. currentmodule:: dagster_postgres.schedule_storage

.. autoclass:: PostgresScheduleStorage
