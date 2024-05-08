Dagster Pipes
=============

Dagster Pipes is a toolkit for building integrations between Dagster and external execution environments. 

This reference contains two sections, one for each part of a Pipes session:

* **Orchestration process** - Reference for Pipes APIs, included with ``dagster`` and meant to be used in the orchestration environment
* **External environment/process** - Reference for the ``dagster-pipes`` library, which should be included in the external process that integrates with Dagster

Refer to the `Dagster Pipes </concepts/dagster-pipes>`_ documentation for more information. For a detailed look at the Pipes process, including how to customize it, refer to the `Dagster Pipes details and customization guide </concepts/dagster-pipes/dagster-pipes-details-and-customization#overview-and-terms>`_.

----

Orchestration process (Dagster)
-------------------------------

.. currentmodule:: dagster

Abstractions for the orchestration side of the Dagster Pipes protocol. **Note**: These APIs are included with the ``dagster`` library.

Sessions
~~~~~~~~

.. autoclass:: PipesSession

.. autofunction:: open_pipes_session

Clients
~~~~~~~

.. autoclass:: PipesClient

.. autoclass:: PipesSubprocessClient

Context injectors
~~~~~~~~~~~~~~~~~

Context injectors write context payloads to an externally accessible location and yield a set of parameters encoding the location for inclusion in the bootstrap payload.

.. autoclass:: PipesContextInjector

.. autoclass:: PipesEnvContextInjector

.. autoclass:: PipesFileContextInjector

.. autoclass:: PipesTempFileContextInjector

Message readers
~~~~~~~~~~~~~~~

Message readers read messages (and optionally log files) from an externally accessible location and yield a set of parameters encoding the location in the bootstrap payload. 

.. autoclass:: PipesMessageReader

.. autoclass:: PipesBlobStoreMessageReader

.. autoclass:: PipesFileMessageReader

.. autoclass:: PipesTempFileMessageReader

.. autoclass:: PipesMessageHandler

----

External process (dagster-pipes)
--------------------------------

.. currentmodule:: dagster_pipes

The ``dagster-pipes`` library is intended for inclusion in an external process that integrates with Dagster using the Pipes protocol. This could be in an environment like Databricks, Kubernetes, or Docker. **Note**: This library isn't included with ``dagster`` and must be `installed separately <https://pypi.org/project/dagster-pipes/>`_.

Refer to the `Dagster Pipes details and customization guide </concepts/dagster-pipes/dagster-pipes-details-and-customization#overview-and-terms>`_ for more information.

Context
~~~~~~~

.. autofunction:: open_dagster_pipes

.. autoclass:: PipesContext

Context loaders
~~~~~~~~~~~~~~~

Context loaders load the context payload from the location specified in the bootstrap payload.

.. autoclass:: PipesContextLoader

.. autoclass:: PipesDefaultContextLoader

.. autoclass:: PipesDbfsContextLoader

Params loaders
~~~~~~~~~~~~~~

Params loaders load the bootstrap payload from some globally accessible key-value store.

.. autoclass:: PipesParamsLoader

.. autoclass:: PipesEnvVarParamsLoader

Message writers
~~~~~~~~~~~~~~~

Message writers write messages to the location specified in the bootstrap payload.

.. autoclass:: PipesMessageWriter

.. autoclass:: PipesDefaultMessageWriter

.. autoclass:: PipesBlobStoreMessageWriter

.. autoclass:: PipesS3MessageWriter

.. autoclass:: PipesDbfsMessageWriter

Message writer channels
~~~~~~~~~~~~~~~~~~~~~~~

Message writer channels are objects that write messages back to the Dagster orchestration process.

.. autoclass:: PipesMessageWriterChannel

.. autoclass:: PipesBlobStoreMessageWriterChannel

.. autoclass:: PipesBufferedFilesystemMessageWriterChannel

.. autoclass:: PipesFileMessageWriterChannel

.. autoclass:: PipesStreamMessageWriterChannel

.. autoclass:: PipesS3MessageWriterChannel

Utilities
~~~~~~~~~

.. autofunction:: encode_env_var

.. autofunction:: decode_env_var

.. autoclass:: DagsterPipesError

.. autoclass:: DagsterPipesWarning