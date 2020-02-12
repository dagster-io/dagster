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
   :members:

.. currentmodule:: dagster.core.storage.event_log

.. autoclass:: EventLogStorage
   :members:

.. autoclass:: SqlEventLogStorage
   :members: connect, upgrade

.. autoclass:: SqliteEventLogStorage

.. currentmodule:: dagster.core.storage.runs

.. autoclass:: RunStorage
   :members:

.. autoclass:: SqlRunStorage
   :members: connect, upgrade

.. autoclass:: SqliteRunStorage

.. currentmodule:: dagster.core.storage.pipeline_run

.. autoclass:: PipelineRun

.. currentmodule:: dagster.core.storage.compute_log_manager

.. autoclass:: ComputeLogManager
   :members:

.. currentmodule:: dagster.core.storage.local_compute_log_manager

.. autoclass:: LocalComputeLogManager

.. currentmodule:: dagster.core.launcher

.. autoclass:: RunLauncher
   :members:

----

.. currentmodule:: dagster.core.storage.compute_log_manager

.. autoclass:: ComputeLogManager
   :members:

Scheduling
----------

.. currentmodule:: dagster.core.scheduler

.. autoclass:: Scheduler
   :members:
