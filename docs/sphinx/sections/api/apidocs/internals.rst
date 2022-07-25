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

Executors
---------
.. autodecorator:: executor

.. autoclass:: ExecutorDefinition
    :members: configured

.. autoclass:: InitExecutorContext
    :members:

.. autoclass:: Executor
    :members:

----

File Manager
--------------

.. currentmodule:: dagster._core.storage.file_manager

.. autoclass:: FileManager
   :members:

.. currentmodule:: dagster

.. autodata:: local_file_manager
   :annotation: ResourceDefinition

----


Instance
--------

.. currentmodule:: dagster

.. autoclass:: DagsterInstance
   :members:

.. currentmodule:: dagster._core.instance

.. autoclass:: InstanceRef
   :members:

.. currentmodule:: dagster._serdes

.. autoclass:: ConfigurableClass
   :members:

.. autoclass:: ConfigurableClassData
   :members:

.. currentmodule:: dagster._core.storage.root

.. autoclass:: LocalArtifactStorage
   :members:

----

Storage
-------

.. currentmodule:: dagster._core.storage.base_storage

.. autoclass:: DagsterStorage

----

Run storage
-----------

.. currentmodule:: dagster

.. autoclass:: PipelineRun

.. autoclass:: DagsterRunStatus
   :members:
   :undoc-members:

.. autoclass:: PipelineRunStatus
   :members:
   :undoc-members:

.. currentmodule:: dagster._core.storage.runs

.. autoclass:: RunStorage

.. autoclass:: SqlRunStorage

.. autoclass:: SqliteRunStorage


See also: :py:class:`dagster_postgres.PostgresRunStorage` and :py:class:`dagster_mysql.MySQLRunStorage`.

----

Event log storage
-----------------

.. currentmodule:: dagster._core.storage.event_log

.. autoclass:: EventLogEntry

.. autoclass:: EventLogRecord

.. autoclass:: EventRecordsFilter

.. autoclass:: RunShardedEventsCursor

.. autoclass:: EventLogStorage

.. autoclass:: SqlEventLogStorage

.. autoclass:: SqliteEventLogStorage

.. autoclass:: ConsolidatedSqliteEventLogStorage

See also: :py:class:`dagster_postgres.PostgresEventLogStorage` and :py:class:`dagster_mysql.MySQLEventLogStorage`.

----

Compute log manager
-------------------

.. currentmodule:: dagster._core.storage.compute_log_manager

.. autoclass:: ComputeLogManager

.. currentmodule:: dagster._core.storage.local_compute_log_manager

.. autoclass:: LocalComputeLogManager

See also: :py:class:`dagster_aws.S3ComputeLogManager`.

----

Run launcher
------------
.. currentmodule:: dagster._core.launcher

.. autoclass:: RunLauncher

.. autoclass:: DefaultRunLauncher

----

Run coordinator
---------------

.. currentmodule:: dagster._core.run_coordinator

.. autoclass:: DefaultRunCoordinator

.. autoconfigurable:: QueuedRunCoordinator
  :annotation: RunCoordinator

----

Scheduling
----------

.. currentmodule:: dagster._core.scheduler

.. autoclass:: Scheduler

.. currentmodule:: dagster._core.storage.schedules

.. autoclass:: ScheduleStorage

.. autoclass:: SqlScheduleStorage

.. autoclass:: SqliteScheduleStorage

see also: :py:class:`dagster_postgres.PostgresScheduleStorage` and :py:class:`dagster_mysql.MySQLScheduleStorage`.

----

Exception handling
------------------

.. currentmodule:: dagster._core.errors

.. autofunction:: user_code_error_boundary
