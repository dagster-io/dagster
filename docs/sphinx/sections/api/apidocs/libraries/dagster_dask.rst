Dask (dagster_dask)
===================

The ``dagster_dask`` module provides support for executing Dagster pipelines in Dask clusters, and using Dask as a resource to perform computations in solids. It also provides a DataFrame type with loaders and materializers so that you can easily work with DataFrames in solids.

See the `Dask deployment guide <https://docs.dagster.io/deploying/dask/>`_ for more information about using Dask for execution.

.. currentmodule:: dagster_dask

Executors
---------

.. autodata:: dask_executor
  :annotation: ExecutorDefinition

Resources
---------

.. autodata:: dask_resource
  :annotation: ResourceDefinition

Types
-----

.. autodata:: DataFrame
