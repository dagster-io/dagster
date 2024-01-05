Polars (dagster-polars)
-----------------------------------------------------

This library allows using ``Polars`` DataFrames as inputs and outputs of Dagster's ``@asset`` and ``@op``.
Type annotations are used to control whether to load an eager or lazy DataFrame.
Remote storage like S3 is supported.

IOManagers
==========

All IOManagers log various metadata about the DataFrame - size, schema, sample, stats.
For all IOManagers the `columns` input metadata can be used to select a subset of columns to load.

BasePolarsUPathIOManager
------------------------

Is a base class for IO managers that store Polars DataFrames in filesystem - local or remote. Shouldn't be used directly unless you want to implement your own `IOManager`. It has the following features (which are inherited by all UPath-based IOManagers in this library):

* inherits all the features of the `UPathIOManager` - works with local and remote filesystems (like S3),
    supports loading multiple partitions (use `dict[str, DataFrame]` type annotation), ...
* sensitive to type annotations. Will load eager or lazy DataFrame based on the type annotation: `polars.DataFrame` or `LazyFrame`.
* `Optional` type annotations are supported. If the input annotation is `Optional` and is missing in the filesystem, the IOManager will skip loading the input and return `None` instead. If the output annotation is `Optional` and the output is `None`, the IOManager will skip writing the output to the filesystem.
* Supports reading/writing arbitrary metadata dict into storage (in contrast to saving Dagster metadata into Dagster's postgres). This metadata can be then accessed outside Dagster. `Tuple[DataFrame/LazyFrame, Dict[str, Any]]` type annotation must be used on the input/output to trigger metadata read/write. This feature is supported by:
    * `PolarsParquetIOManager` - metadata is saved in the Parquet file's schema metadata as json-serialized bytes at "dagster_polars_storage_metadata" key.
    * `PolarsDeltaIOManager` - metadata is saved in `<table>/.dagster_polars_metadata/<version>.json` file.

The following typing aliases are provided for convenience:
* `StorageMetadata` = `Dict[str, Any]`
* `DataFramePartitions` = `Dict[str, DataFrame]`
* `LazyFramePartitions` = `Dict[str, LazyFrame]`
* `DataFrameWithMetadata` = `Tuple[DataFrame, StorageMetadata]`
* `LazyFrameWithMetadata` = `Tuple[LazyFrame, StorageMetadata]`
* `DataFramePartitionsWithMetadata` = `Dict[str, DataFrameWithMetadata]`
* `LazyFramePartitionsWithMetadata` = `Dict[str, LazyFrameWithMetadata]`

Complete description of `dagster_polars` behavior for all supported type annotations:

|+--------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Type annotation                      | Behavior                                                                                                                                                                                                              |
+======================================+=======================================================================================================================================================================================================================+
| `DataFrame`                         | read/write DataFrame. Raise error if it's not found in storage.                                                                                                                                                       |
+--------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| `LazyFrame`                         | read LazyFrame. Raise error if it's not found in storage.                                                                                                                                                             |
+--------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| `Optional[DataFrame]`               | read/write DataFrame. Skip if it's not found in storage or the output is `None`.                                                                                                                                      |
+--------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| `Optional[LazyFrame]`               | read LazyFrame. Skip if it's not found in storage                                                                                                                                                                     |
+--------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| `DataFrameWithMetadata`             | read/write DataFrame and metadata. Raise error if it's not found in storage.                                                                                                                                          |
+--------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| `LazyFrameWithMetadata`             | read LazyFrame and metadata. Raise error if it's not found in storage.                                                                                                                                                |
+--------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| `Optional[DataFrameWithMetadata]`   | read/write DataFrame and metadata. Skip if it's not found in storage or the output is `None`.                                                                                                                         |
+--------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| `Optional[LazyFrameWithMetadata]`   | read LazyFrame and metadata. Skip if it's not found in storage.                                                                                                                                                       |
+--------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| `DataFramePartitions`               | read multiple DataFrames as `Dict[str, DataFrame]`. Raise an error if any of thems is not found in storage, unless `"allow_missing_partitions"` input metadata is set to `True`                                      |
+--------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| `LazyFramePartitions`               | read multiple LazyFrames as `Dict[str, LazyFrame]`. Raise an error if any of thems is not found in storage, unless `"allow_missing_partitions"` input metadata is set to `True`                                      |
+--------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| `DataFramePartitionsWithMetadata`   | read multiple DataFrames and metadata as `Dict[str, Tuple[DataFrame, StorageMetadata]]`. Raise an error if any of thems is not found in storage, unless `"allow_missing_partitions"` input metadata is set to `True` |
+--------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| `LazyFramePartitionsWithMetadata`   | read multiple LazyFrames and metadata as `Dict[str, Tuple[LazyFrame, StorageMetadata]]`. Raise an error if any of thems is not found in storage, unless `"allow_missing_partitions"` input metadata is set to `True` |
+--------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Generic builtins (like `tuple[...]` instead of `Tuple[...]`) are supported for Python >= 3.9.

`PolarsParquetIOManager`
------------------------

Implements reading and writing files in Apache Parquet format. Supports reading partitioned Parquet datasets (for example, often produced by Spark). All read/write options can be set via Dagster metadata values. Supports writing/reading custom metadata into the Parquet file's schema metadata.

`PolarsDeltaIOManager`
------------------------

`PolarsDeltaIOManager` - IOManager for reading and writing Delta Lake tables. All read/write options can be set via Dagster metadata values. `mode`, `overwrite_schema` and `version` can be set via config parameters. `partition_by` can be set to use native Delta Lake partitioning (it's passed to `delta_write_options` of `write_delta`). The IOManager won't manage partitioning in this case, and all the asset partitions will be stored in the same Delta Table directory. You are responsible for filtering correct partitions when reading the data in the downstream assets. Required dependencies can be installed with `pip install 'dagster-polars[deltalake]'`. Supports writing/reading custom metadata to/from the DeltaTable directory.


`BigQueryPolarsIOManager`
---------------------------
Implements reading and writing data from/to [BigQuery](https://cloud.google.com/bigquery). Supports writing partitioned tables (`"partition_expr"` input metadata key must be specified). Required dependencies can be installed with `pip install 'dagster-polars[gcp]'`.


.. currentmodule:: dagster_polars

.. autoconfigurable:: PolarsParquetIOManager
  :annotation: IOManagerDefinition

.. autoconfigurable:: PolarsDeltaIOManager
  :annotation: IOManagerDefinition

.. autoconfigurable:: BigQueryPolarsIOManager
  :annotation: IOManagerDefinition
