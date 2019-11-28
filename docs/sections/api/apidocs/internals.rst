Internals
=========

.. currentmodule:: dagster

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

System Storage
--------------
.. autodecorator:: system_storage

.. autoclass:: SystemStorageDefinition

.. currentmodule:: dagster.core.storage.system_storage

Instance
--------

.. currentmodule:: dagster.core.instance

.. autoclass:: DagsterInstance
   :members:

.. currentmodule:: dagster.core.storage.root

.. autoclass:: LocalArtifactStorage

.. currentmodule:: dagster.core.storage.event_log

.. autoclass:: EventLogStorage

.. currentmodule:: dagster.core.storage.runs

.. autoclass:: RunStorage

Scheduling
----------

.. currentmodule:: dagster.core.scheduler

.. autoclass:: Scheduler
