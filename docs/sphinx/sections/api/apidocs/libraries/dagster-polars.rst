Polars (dagster-polars)
-----------------------------------------------------

This library allows using `Polars` DataFrames as inputs and outputs for Dagster's `@asset` and `@op`.
Type annotations are used to control whether to load an eager or lazy DataFrame.
Supports multiple serialization formats (Parquet, Delta Lake, BigQuery) and filesystems (local, S3, GCS, ...).

The following typing aliases are provided for convenience:
 - `StorageMetadata` = `Dict[str, Any]`
 - `DataFramePartitions` = `Dict[str, DataFrame]`
 - `LazyFramePartitions` = `Dict[str, LazyFrame]`
 - `DataFrameWithMetadata` = `Tuple[DataFrame, StorageMetadata]`
 - `LazyFrameWithMetadata` = `Tuple[LazyFrame, StorageMetadata]`
 - `DataFramePartitionsWithMetadata` = `Dict[str, DataFrameWithMetadata]`
 - `LazyFramePartitionsWithMetadata` = `Dict[str, LazyFrameWithMetadata]`

.. list-table::  behavior for supported type annotations
   :widths: 25 50
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

.. currentmodule:: dagster_polars

.. autoconfigurable:: BasePolarsUPathIOManager
  :annotation: IOManagerDefinition

.. autoconfigurable:: PolarsParquetIOManager
  :annotation: IOManagerDefinition

.. autoconfigurable:: PolarsDeltaIOManager
  :annotation: IOManagerDefinition

.. autoconfigurable:: BigQueryPolarsIOManager
  :annotation: IOManagerDefinition


Required dependencies can be installed with `pip install 'dagster-polars[deltalake]'`. Supports writing/reading custom metadata to/from the DeltaTable directory.

Implements reading and writing data from/to `BigQuery <https://cloud.google.com/bigquery>`_). Supports writing partitioned tables (`"partition_expr"` input metadata key must be specified). Required dependencies can be installed with `pip install 'dagster-polars[gcp]'`.

