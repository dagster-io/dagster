Pipes (dagster-pipes)
=====================

.. currentmodule:: dagster_pipes

The ``dagster-pipes`` library is intended for inclusion in an external process that integrates with Dagster using the `Pipes <https://docs.dagster.io/concepts/dagster-pipes>`_ protocol. This could be in an environment like Databricks, Kubernetes, or Docker. Using this library, you can write code in the external process that streams metadata back to Dagster.

For a detailed look at the Pipes process, including how to customize it, refer to the `Dagster Pipes details and customization guide <https://docs.dagster.io/concepts/dagster-pipes/dagster-pipes-details-and-customization#overview-and-terms>`__.

**Looking to set up a Pipes client in Dagster?** Refer to the `Dagster Pipes API reference <https://docs.dagster.io/_apidocs/pipes>`_.

**Note**: This library isn't included with ``dagster`` and must be `installed separately <https://pypi.org/project/dagster-pipes/>`_.

----

Context
-------

.. autofunction:: open_dagster_pipes

.. autoclass:: PipesContext

----

Advanced
--------

Most Pipes users won't need to use the APIs in the following sections unless they are customizing the Pipes protocol.

Refer to the `Dagster Pipes details and customization guide <https://docs.dagster.io/concepts/dagster-pipes/dagster-pipes-details-and-customization#overview-and-terms>`__ for more information.

Context loaders
^^^^^^^^^^^^^^^

Context loaders load the context payload from the location specified in the bootstrap payload.

.. autoclass:: PipesContextLoader

.. autoclass:: PipesDefaultContextLoader

.. autoclass:: PipesDbfsContextLoader

----

Params loaders
^^^^^^^^^^^^^^

Params loaders load the bootstrap payload from some globally accessible key-value store.

.. autoclass:: PipesParamsLoader

.. autoclass:: PipesEnvVarParamsLoader

.. autoclass:: PipesCliArgsParamsLoader

----

Message writers
^^^^^^^^^^^^^^^

Message writers write messages to the location specified in the bootstrap payload.

.. autoclass:: PipesMessageWriter

.. autoclass:: PipesDefaultMessageWriter

.. autoclass:: PipesBlobStoreMessageWriter

.. autoclass:: PipesS3MessageWriter

.. autoclass:: PipesDbfsMessageWriter

----

Message writer channels
^^^^^^^^^^^^^^^^^^^^^^^

Message writer channels are objects that write messages back to the Dagster orchestration process.

.. autoclass:: PipesMessageWriterChannel

.. autoclass:: PipesBlobStoreMessageWriterChannel

.. autoclass:: PipesBufferedFilesystemMessageWriterChannel

.. autoclass:: PipesFileMessageWriterChannel

.. autoclass:: PipesStreamMessageWriterChannel

.. autoclass:: PipesS3MessageWriterChannel

----

Utilities
^^^^^^^^^

.. autofunction:: encode_env_var

.. autofunction:: decode_env_var

.. autoclass:: DagsterPipesError

.. autoclass:: DagsterPipesWarning