Internals
=========

.. currentmodule:: dagster

|
Please note that internal APIs are likely to be in much greater flux pre-1.0 than user-facing APIs,
particularly if not exported in the top level ``dagster`` module.

|
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

.. autoclass:: Executor
    :members:

----

System Storage
--------------
.. autodecorator:: system_storage

.. autoclass:: SystemStorageDefinition

.. autoclass:: InitSystemStorageContext
   :members:

.. currentmodule:: dagster.core.storage.system_storage

.. autoclass:: SystemStorageData

.. currentmodule:: dagster.core.storage.file_manager

.. autoclass:: FileManager
   :members:

.. autoclass:: LocalFileManager

----


Intermediate Storage
--------------------
.. currentmodule:: dagster

.. autodecorator:: intermediate_storage

.. autoclass:: IntermediateStorageDefinition

.. autoclass:: InitIntermediateStorageContext
   :members:

.. currentmodule:: dagster.core.storage.system_storage

.. autoclass:: IntermediateStorage

----

Instance
--------

.. currentmodule:: dagster

.. autoclass:: DagsterInstance
   :members:

.. currentmodule:: dagster.core.instance

.. autoclass:: InstanceRef
   :members:

.. currentmodule:: dagster.serdes

.. autoclass:: ConfigurableClass
   :members:

.. autoclass:: ConfigurableClassData
   :members:

.. currentmodule:: dagster.core.storage.root

.. autoclass:: LocalArtifactStorage
   :members:

----

Run storage
-----------

.. currentmodule:: dagster

.. autoclass:: PipelineRun

.. currentmodule:: dagster.core.storage.runs

.. autoclass:: RunStorage

.. autoclass:: SqlRunStorage

.. autoclass:: SqliteRunStorage


See also: :py:class:`dagster_postgres.PostgresRunStorage`.

----

Event log storage
-----------------

.. currentmodule:: dagster.core.storage.event_log

.. autoclass:: EventLogStorage

.. autoclass:: SqlEventLogStorage

.. autoclass:: SqliteEventLogStorage

See also: :py:class:`dagster_postgres.PostgresEventLogStorage`.

----

Compute log manager
-------------------

.. currentmodule:: dagster.core.storage.compute_log_manager

.. autoclass:: ComputeLogManager

.. currentmodule:: dagster.core.storage.local_compute_log_manager

.. autoclass:: LocalComputeLogManager

See also: :py:class:`dagster_aws.S3ComputeLogManager`.

----

Run launcher
------------
.. currentmodule:: dagster.core.launcher

.. autoclass:: RunLauncher

.. autoclass:: DefaultRunLauncher

.. currentmodule:: dagster_graphql.launcher

See also: :py:class:`dagster_k8s.K8sRunLauncher`.

----

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

See also: :py:class:`dagster_postgres.PostgresScheduleStorage`.

----

Exception handling
------------------

.. currentmodule:: dagster.core.errors

.. autofunction:: user_code_error_boundary

----

Architecture
------------

Details of internal architecture captured at a specific point in time. These are expected to only be
useful to people working on dagster core or complex libraries/integrations.

Pipeline Execution Flow - March 2020 (0.7.6)
********************************************

.. image:: //assets/images/apidocs/internal/execution_flow.png
    :scale: 40 %
    :align: center