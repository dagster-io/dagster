import json
from typing import TYPE_CHECKING, Any, Optional, Union

import polars as pl
import pyarrow as pa
import pyarrow.dataset
import pyarrow.parquet
from dagster import InputContext, OutputContext
from dagster._annotations import experimental
from packaging.version import Version
from pyarrow import Table

from dagster_polars.io_managers.base import BasePolarsUPathIOManager
from dagster_polars.types import LazyFrameWithMetadata, StorageMetadata

if TYPE_CHECKING:
    import fsspec
    from upath import UPath


DAGSTER_POLARS_STORAGE_METADATA_KEY = "dagster_polars_metadata"


def get_pyarrow_dataset(path: "UPath", context: InputContext) -> pyarrow.dataset.Dataset:
    assert context.metadata is not None

    fs: Union[fsspec.AbstractFileSystem, None] = None

    try:
        fs = path.fs
    except AttributeError:
        pass

    ds = pyarrow.dataset.dataset(
        str(path),
        filesystem=fs,
        format=context.metadata.get("format", "parquet"),
        partitioning=context.metadata.get("partitioning"),
        partition_base_dir=context.metadata.get("partition_base_dir"),
        exclude_invalid_files=context.metadata.get("exclude_invalid_files", True),
        ignore_prefixes=context.metadata.get("ignore_prefixes", [".", "_"]),
    )

    return ds


def scan_parquet_legacy(path: "UPath", context: InputContext) -> pl.LazyFrame:
    """Scan a parquet file and return a lazy frame (uses pyarrow).

    :param path:
    :param context:
    :return:
    """
    assert context.metadata is not None

    ldf = pl.scan_pyarrow_dataset(
        get_pyarrow_dataset(path, context),
        allow_pyarrow_filter=context.metadata.get("allow_pyarrow_filter", True),
    )

    return ldf


def scan_parquet(path: "UPath", context: InputContext) -> pl.LazyFrame:
    """Scan a parquet file and return a lazy frame (uses polars native reader).

    :param path:
    :param context:
    :return:
    """
    assert context.metadata is not None

    storage_options: Optional[dict[str, Any]] = None

    try:
        storage_options = path.storage_options
    except AttributeError:
        # TODO: explore removing this as universal-pathlib should always provide storage_options in newer versions
        pass

    kwargs = dict(
        n_rows=context.metadata.get("n_rows", None),
        cache=context.metadata.get("cache", True),
        parallel=context.metadata.get("parallel", "auto"),
        rechunk=context.metadata.get("rechunk", True),
        row_count_name=context.metadata.get("row_count_name", None),
        row_count_offset=context.metadata.get("row_count_offset", 0),
        low_memory=context.metadata.get("low_memory", False),
        use_statistics=context.metadata.get("use_statistics", True),
    )

    if Version(pl.__version__) > Version("0.19.4"):
        kwargs["hive_partitioning"] = context.metadata.get("hive_partitioning", True)
        kwargs["retries"] = context.metadata.get("retries", 0)

    return pl.scan_parquet(str(path), storage_options=storage_options, **kwargs)  # type: ignore


@experimental
class PolarsParquetIOManager(BasePolarsUPathIOManager):
    """Implements reading and writing Polars DataFrames in Apache Parquet format.

    Features:
     - All features provided by :py:class:`~dagster_polars.BasePolarsUPathIOManager`.
     - All read/write options can be set via corresponding metadata or config parameters (metadata takes precedence).
     - Supports reading partitioned Parquet datasets (for example, often produced by Spark).
     - Supports reading/writing custom metadata in the Parquet file's schema as json-serialized bytes at `"dagster_polars_metadata"` key.

    Examples:

        .. code-block:: python

            from dagster import asset
            from dagster_polars import PolarsParquetIOManager
            import polars as pl

            @asset(
                io_manager_key="polars_parquet_io_manager",
                key_prefix=["my_dataset"]
            )
            def my_asset() -> pl.DataFrame:  # data will be stored at <base_dir>/my_dataset/my_asset.parquet
                ...

            defs = Definitions(
                assets=[my_table],
                resources={
                    "polars_parquet_io_manager": PolarsParquetIOManager(base_dir="s3://my-bucket/my-dir")
                }
            )

        Reading partitioned Parquet datasets:

        .. code-block:: python

            from dagster import SourceAsset

            my_asset = SourceAsset(
                key=["path", "to", "dataset"],
                io_manager_key="polars_parquet_io_manager",
                metadata={
                    "partitioning": ["year", "month", "day"]
                }
            )

        Storing custom metadata in the Parquet file schema (this metadata can be read outside of Dagster with a helper function :py:meth:`dagster_polars.PolarsParquetIOManager.read_parquet_metadata`):

        .. code-block:: python

            from dagster_polars import DataFrameWithMetadata


            @asset(
                io_manager_key="polars_parquet_io_manager",
            )
            def upstream() -> DataFrameWithMetadata:
                return pl.DataFrame(...), {"my_custom_metadata": "my_custom_value"}


            @asset(
                io_manager_key="polars_parquet_io_manager",
            )
            def downsteam(upstream: DataFrameWithMetadata):
                df, metadata = upstream
                assert metadata["my_custom_metadata"] == "my_custom_value"
    """

    extension: str = ".parquet"  # type: ignore
    use_legacy_reader: bool = False

    def dump_df_to_path(
        self,
        context: OutputContext,
        df: pl.DataFrame,
        path: "UPath",
        metadata: Optional[StorageMetadata] = None,
    ):
        assert context.metadata is not None

        table: Table = df.to_arrow()

        if metadata is not None:
            existing_metadata = table.schema.metadata.to_dict() if table.schema.metadata is not None else {}
            existing_metadata.update({DAGSTER_POLARS_STORAGE_METADATA_KEY: json.dumps(metadata)})
            table = table.replace_schema_metadata(existing_metadata)

        compression = context.metadata.get("compression", "zstd")
        compression_level = context.metadata.get("compression_level")
        statistics = context.metadata.get("statistics", False)
        row_group_size = context.metadata.get("row_group_size")
        pyarrow_options = context.metadata.get("pyarrow_options", None)

        if pyarrow_options is not None and pyarrow_options.get("partition_cols"):
            pyarrow_options["compression"] = None if compression == "uncompressed" else compression
            pyarrow_options["compression_level"] = compression_level
            pyarrow_options["write_statistics"] = statistics
            pyarrow_options["row_group_size"] = row_group_size

            assert isinstance(table, Table)

            pa.parquet.write_to_dataset(
                table=table,
                root_path=str(path),
                **(pyarrow_options or {}),
            )
        else:
            assert isinstance(table, Table)
            pa.parquet.write_table(
                table=table,
                where=str(path),
                row_group_size=row_group_size,
                compression=None if compression == "uncompressed" else compression,
                compression_level=compression_level,
                write_statistics=statistics,
                filesystem=(path.fs if hasattr(path, "fs") else None),
                **(pyarrow_options or {}),
            )

    def scan_df_from_path(  # type: ignore
        self, path: "UPath", context: InputContext, with_metadata: Optional[bool] = False
    ) -> Union[pl.LazyFrame, LazyFrameWithMetadata]:
        assert context.metadata is not None

        if self.use_legacy_reader or Version(pl.__version__) < Version("0.19.4"):
            ldf = scan_parquet_legacy(path, context)
        else:
            ldf = scan_parquet(path, context)

        if not with_metadata:
            return ldf
        else:
            ds = get_pyarrow_dataset(path, context)
            dagster_polars_metadata = (
                ds.schema.metadata.get(DAGSTER_POLARS_STORAGE_METADATA_KEY.encode("utf-8"))
                if ds.schema.metadata is not None
                else None
            )

            metadata = json.loads(dagster_polars_metadata) if dagster_polars_metadata is not None else {}

            return ldf, metadata

    @classmethod
    def read_parquet_metadata(cls, path: "UPath") -> StorageMetadata:
        """Just a helper method to read metadata from a parquet file.

        Is not used internally, but is helpful for reading Parquet metadata from outside of Dagster.
        :param path:
        :return:
        """
        metadata = pyarrow.parquet.read_metadata(
            str(path), filesystem=path.fs if hasattr(path, "fs") else None
        ).metadata

        dagster_polars_metadata = (
            metadata.get(DAGSTER_POLARS_STORAGE_METADATA_KEY.encode("utf-8")) if metadata is not None else None
        )

        return json.loads(dagster_polars_metadata) if dagster_polars_metadata is not None else {}
