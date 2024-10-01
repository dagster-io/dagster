Dagster Pipes
=============

.. currentmodule:: dagster

`Dagster Pipes <https://docs.dagster.io/concepts/dagster-pipes>`_  is a toolkit for building integrations between Dagster and external execution environments. This reference outlines the APIs included with the ``dagster`` library, which should be used in the orchestration environment.

For a detailed look at the Pipes process, including how to customize it, refer to the `Dagster Pipes details and customization guide <https://docs.dagster.io/concepts/dagster-pipes/dagster-pipes-details-and-customization#overview-and-terms>`__.

**Looking to write code in an external process?** Refer to the API reference for the separately-installed `dagster-pipes <https://docs.dagster.io/_apidocs/libraries/dagster-pipes>`_ library. 

----

Sessions
--------

.. autoclass:: PipesSession

.. autofunction:: open_pipes_session

.. currentmodule:: dagster._core.pipes.subprocess

----

Clients
-------

.. currentmodule:: dagster

.. autoclass:: PipesClient

.. autoclass:: PipesSubprocessClient

----

Advanced
--------

Most Pipes users won't need to use the APIs in the following sections unless they are customizing the Pipes protocol.

Refer to the `Dagster Pipes details and customization guide <https://docs.dagster.io/concepts/dagster-pipes/dagster-pipes-details-and-customization#overview-and-terms>`__ for more information.

Context injectors
^^^^^^^^^^^^^^^^^

Context injectors write context payloads to an externally accessible location and yield a set of parameters encoding the location for inclusion in the bootstrap payload.

.. autoclass:: PipesContextInjector

.. autoclass:: PipesEnvContextInjector

.. autoclass:: PipesFileContextInjector

.. autoclass:: PipesTempFileContextInjector

----

Message readers
^^^^^^^^^^^^^^^

Message readers read messages (and optionally log files) from an externally accessible location and yield a set of parameters encoding the location in the bootstrap payload. 

.. autoclass:: PipesMessageReader

.. autoclass:: PipesBlobStoreMessageReader

.. autoclass:: PipesFileMessageReader

.. autoclass:: PipesTempFileMessageReader

.. autoclass:: PipesMessageHandler
