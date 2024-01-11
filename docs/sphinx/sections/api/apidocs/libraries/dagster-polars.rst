.. currentmodule:: dagster_polars

Polars (dagster-polars)
-----------------------------------------------------

This library provides Dagster integration with `Polars <https://pola.rs>`_.
It allows using Polars DataFrames as inputs and outputs with Dagster's `@asset` and `@op`.
Type annotations are used to control whether to load an eager or lazy DataFrame.
Multiple serialization formats (Parquet, Delta Lake, BigQuery) and filesystems (local, S3, GCS, ...) are supported.

Related Guides:

* `Using Dagster with Polars tutorial </integrations/polars>`_

Installation
~~~~~~~~~~~~
.. code-block::

    pip install dagster-polars


Some IOManagers (like :py:class:`PolarsDeltaIOManager`) may require additional dependencies, which are provided with extras like `dagster-polars[delta]`.
Please check the documentation for each IOManager for more details.

Quickstart
~~~~~~~~~~

Common filesystem-based IOManagers features highlights, using :py:class:`PolarsParquetIOManager` as an example (check :py:class:`BasePolarsUPathIOManager` for more details):

Type annotations are not required. By default an eager `pl.DataFrame` will be loaded.

.. code-block:: python

    from dagster import asset
    from dagster_polars import PolarsParquetIOManager
    import polars as pl

    @asset(io_manager_key="polars_parquet_io_manager")
    def upstream():
        return DataFrame({"foo": [1, 2, 3]})

    @asset
    def downstream(upstream):
        assert isinstance(upstream, pl.DataFrame)

Lazy `pl.LazyFrame` can be loaded by annotating the input with `LazyFrame`:

.. code-block:: python

    @asset(io_manager_key="polars_parquet_io_manager")
    def downstream(upstream: LazyFrame):
        assert isinstance(upstream, pl.LazyFrame)

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

Some IOManagers support saving/loading custom metadata along with the DataFrame. This is often useful for external systems which read the data outside of Dagster.

.. code-block:: python

    from dagster_polars import DataFrameWithMetadata

    @asset
    def downstream(upstream: DataFrameWithMetadata):
        df, metadata = upstream
        assert isinstance(upstream[0], pl.DataFrame)
        assert isinstance(upstream[1], dict)

The following typing aliases are provided by :py:mod:`dagster_polars.types` for convenience:
 - `StorageMetadata` = `Dict[str, Any]`
 - `DataFramePartitions` = `Dict[str, DataFrame]`
 - `LazyFramePartitions` = `Dict[str, LazyFrame]`
 - `DataFrameWithMetadata` = `Tuple[DataFrame, StorageMetadata]`
 - `LazyFrameWithMetadata` = `Tuple[LazyFrame, StorageMetadata]`
 - `DataFramePartitionsWithMetadata` = `Dict[str, DataFrameWithMetadata]`
 - `LazyFramePartitionsWithMetadata` = `Dict[str, LazyFrameWithMetadata]`

.. list-table::  behavior for supported type annotations
   :widths: 25 75
   :header-rows: 1

   * - Type annotation
     - Behavior
   * - `DataFrame`
     - read/write DataFrame. Raise error if it's not found in storage.
   * - `LazyFrame`
     - read LazyFrame. Raise error if it's not found in storage.
   * - `Optional[DataFrame]`
     - read/write DataFrame. Skip if it's not found in storage or the output is `None`.
   * - `Optional[LazyFrame]`
     - read LazyFrame. Skip if it's not found in storage.
   * - `DataFrameWithMetadata`
     - read/write DataFrame and metadata. Raise error if it's not found in storage.
   * - `LazyFrameWithMetadata`
     - read LazyFrame and metadata. Raise error if it's not found in storage.
   * - `Optional[DataFrameWithMetadata]`
     - read/write DataFrame and metadata. Skip if it's not found in storage or the output is `None`.
   * - `Optional[LazyFrameWithMetadata]`
     - read LazyFrame and metadata. Skip if it's not found in storage.
   * - `DataFramePartitions`
     - read multiple DataFrames as `Dict[str, DataFrame]`. Raise an error if any of thems is not found in storage, unless `"allow_missing_partitions"` input metadata is set to `True`
   * - `LazyFramePartitions`
     - read multiple LazyFrames as `Dict[str, LazyFrame]`. Raise an error if any of thems is not found in storage, unless `"allow_missing_partitions"` input metadata is set to `True`
   * - `DataFramePartitionsWithMetadata`
     - read multiple DataFrames and metadata as `Dict[str, Tuple[DataFrame, StorageMetadata]]`. Raise an error if any of thems is not found in storage, unless `"allow_missing_partitions"` input metadata is set to `True`
   * - `LazyFramePartitionsWithMetadata`
     - read multiple LazyFrames and metadata as `Dict[str, Tuple[LazyFrame, StorageMetadata]]`. Raise an error if any of thems is not found in storage, unless `"allow_missing_partitions"` input metadata is set to `True`

Generic builtins (like `tuple[...]` instead of `Tuple[...]`) are supported for Python >= 3.9.

.. autoconfigurable:: BasePolarsUPathIOManager
  :annotation: IOManagerDefinition

.. autoconfigurable:: PolarsParquetIOManager
  :annotation: IOManagerDefinition

.. autoconfigurable:: PolarsDeltaIOManager
  :annotation: IOManagerDefinition

.. autoconfigurable:: PolarsBigQueryIOManager
  :annotation: IOManagerDefinition
