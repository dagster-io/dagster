.. currentmodule:: dagster_polars

Polars (dagster-polars)
-----------------------------------------------------

This library provides Dagster integration with `Polars <https://pola.rs>`_.
It allows using Polars eager or lazy DataFrames as inputs and outputs with Dagster's `@asset` and `@op`.
Type annotations are used to control whether to load an eager or lazy DataFrame. Lazy DataFrames can be sinked as output.
Multiple serialization formats (Parquet, Delta Lake, BigQuery) and filesystems (local, S3, GCS, ...) are supported.

Comprehensive list of `dagster-polars` behavior for supported type annotations can be found in :ref:`Types` section.

Installation
------------
.. code-block::

    pip install dagster-polars


Some IOManagers (like :py:class:`PolarsDeltaIOManager`) may require additional dependencies, which are provided with extras like `dagster-polars[delta]`.
Please check the documentation for each IOManager for more details.

Quickstart
----------

Common filesystem-based IOManagers features highlights, using :py:class:`PolarsParquetIOManager` as an example (see :py:class:`BasePolarsUPathIOManager` for the full list of features provided by `dagster-polars`):

Type annotations are not required. By default an eager `pl.DataFrame` will be loaded.

.. code-block:: python

    from dagster import asset
    import polars as pl

    @asset(io_manager_key="polars_parquet_io_manager")
    def upstream():
        return DataFrame({"foo": [1, 2, 3]})

    @asset(io_manager_key="polars_parquet_io_manager")
    def downstream(upstream) -> pl.LazyFrame:
        assert isinstance(upstream, pl.DataFrame)
        return upstream.lazy()  # LazyFrame will be sinked

Lazy `pl.LazyFrame` can be scanned by annotating the input with `pl.LazyFrame`, and returning a `pl.LazyFrame` will sink it:

.. code-block:: python

    @asset(io_manager_key="polars_parquet_io_manager")
    def downstream(upstream: pl.LazyFrame) -> pl.LazyFrame:
        assert isinstance(upstream, pl.LazyFrame)
        return upstream

The same logic applies to partitioned assets:

.. code-block:: python

    @asset
    def downstream(partitioned_upstream: Dict[str, pl.LazyFrame]):
        assert isinstance(partitioned_upstream, dict)
        assert isinstance(partitioned_upstream["my_partition"], pl.LazyFrame)

`Optional` inputs and outputs are supported:

.. code-block:: python

    @asset
    def upstream() -> Optional[pl.DataFrame]:
        if has_data:
            return DataFrame({"foo": [1, 2, 3]})  # type check will pass
        else:
            return None  # type check will pass and `dagster_polars` will skip writing the output completely

    @asset
    def downstream(upstream: Optional[pl.LazyFrame]):  # upstream will be None if it doesn't exist in storage
        ...


By default all the IOManagers store separate partitions as physically separated locations, such as:

* `/my/asset/key/partition_0.extension`
* `/my/asset/key/partition_1.extension`


This mode is useful for e.g. snapshotting.

Some IOManagers (like :py:class:`~dagster_polars.PolarsDeltaIOManager`) support reading and writing partitions in storage-native format in the same location.
This mode can be typically enabled by setting `"partition_by"` metadata value. For example, :py:class:`~dagster_polars.PolarsDeltaIOManager` would store different partitions in the same `/my/asset/key.delta` directory, which will be properly partitioned.

This mode should be preferred for true partitioning.

.. _Types:

Type Annotations
----------------

Type aliases like `DataFrameWithPartitions` are provided by :py:mod:`dagster_polars.types` for convenience.

.. list-table:: Supported type annotations and `dagster-polars` behavior
   :widths: 25 10 75
   :header-rows: 1

   * - Type annotation
     - Type Alias
     - Behavior
   * - `DataFrame`
     -
     - read/write a `DataFrame`
   * - `LazyFrame`
     -
     - read/sink a `LazyFrame`
   * - `Optional[DataFrame]`
     -
     - read/write a `DataFrame`. Do nothing if no data is found in storage or the output is `None`
   * - `Optional[LazyFrame]`
     -
     - read a `LazyFrame`. Do nothing if no data is found in storage
   * - `Dict[str, DataFrame]`
     - `DataFrameWithPartitions`
     - read multiple `DataFrame`s as `Dict[str, DataFrame]`. Raises an error for missing partitions, unless `"allow_missing_partitions"` input metadata is set to `True`
   * - `Dict[str, LazyFrame]`
     - `LazyFramePartitions`
     - read multiple `LazyFrame`s as `Dict[str, LazyFrame]`. Raises an error for missing partitions, unless `"allow_missing_partitions"` input metadata is set to `True`

Generic builtins (like `tuple[...]` instead of `Tuple[...]`) are supported for Python >= 3.9.

API Documentation
-----------------

.. autoconfigurable:: BasePolarsUPathIOManager
  :annotation: IOManagerDefinition

.. autoconfigurable:: PolarsParquetIOManager
  :annotation: IOManagerDefinition

.. autoconfigurable:: PolarsDeltaIOManager
  :annotation: IOManagerDefinition

.. autoconfigurable:: PolarsBigQueryIOManager
  :annotation: IOManagerDefinition
