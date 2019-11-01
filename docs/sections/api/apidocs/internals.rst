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

.. autodata:: default_system_storage_defs
   :annotation: [mem_system_storage_def, fs_system_storage_def]

Instance
--------

.. currentmodule:: dagster.core.instance

.. autoclass:: DagsterInstance
   :members:

.. currentmodule:: dagster.core.storage.root

.. autoclass:: LocalArtifactStorage

.. currentmodule:: dagster.core.storage.event_log

.. autoclass:: EventLogStorage

.. currentmodule:: dagster.core.storage.run_storage_abc

.. autoclass:: RunStorage
