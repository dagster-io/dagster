Dagster Pipes
=============

Dagster Pipes is a toolkit for building integrations between Dagster and external execution environments. This reference contains two sections, one for each side of the orchestration process:

* **Orchestration environment** - Reference for Pipes APIs, included with ``dagster`` and meant to be used in the orchestration environment
* **External process** - Reference for the ``dagster-pipes`` library, which should be included in the external process that integrates with Dagster


Orchestration (Dagster)
-----------------------

.. currentmodule:: dagster

Abstractions for the orchestration side of the Dagster Pipes protocol. *Note*: These APIs are included with the ``dagster`` library.

.. autoclass:: PipesClient

.. autoclass:: PipesSubprocessClient

.. autoclass:: PipesContextInjector

.. autoclass:: PipesMessageReader

.. autoclass:: PipesMessageHandler

.. autoclass:: PipesSession

.. autoclass:: PipesBlobStoreMessageReader

.. autoclass:: PipesEnvContextInjector

.. autoclass:: PipesFileContextInjector

.. autoclass:: PipesFileMessageReader

.. autoclass:: PipesTempFileContextInjector

.. autoclass:: PipesTempFileMessageReader

.. autofunction:: open_pipes_session

External process (dagster-pipes)
--------------------------------

.. currentmodule:: dagster_pipes

This library is intended for inclusion in an external process that integrates
with Dagster using the Pipes protocol. TODO: Something about installation?

.. autofunction:: open_dagster_pipes

.. autoclass:: PipesContext

.. autoclass:: DagsterPipesError

.. autoclass:: DagsterPipesWarning

.. autofunction:: encode_env_var

.. autofunction:: decode_env_var

.. autoclass:: PipesContextLoader

.. autoclass:: PipesMessageWriter

.. autoclass:: PipesMessageWriterChannel

.. autoclass:: PipesParamsLoader

.. autoclass:: PipesBlobStoreMessageWriter

.. autoclass:: PipesBlobStoreMessageWriterChannel

.. autoclass:: PipesBufferedFilesystemMessageWriterChannel

.. autoclass:: PipesDefaultContextLoader

.. autoclass:: PipesDefaultMessageWriter

.. autoclass:: PipesFileMessageWriterChannel

.. autoclass:: PipesStreamMessageWriterChannel

.. autoclass:: PipesEnvVarParamsLoader

.. autoclass:: PipesS3MessageWriter

.. autoclass:: PipesS3MessageWriterChannel

.. autoclass:: PipesDbfsContextLoader

.. autoclass:: PipesDbfsMessageWriter
