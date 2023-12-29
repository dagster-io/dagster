import json
from typing import TYPE_CHECKING, Any, Optional, Union

import polars as pl
import pyarrow as pa
import pyarrow.dataset
import pyarrow.parquet
from dagster import InputContext, OutputContext
from packaging.version import Version
from pyarrow import Table
from upath import UPath

from dagster_polars.constants import DAGSTER_POLARS_STORAGE_METADATA_KEY
from dagster_polars.io_managers.base import BasePolarsUPathIOManager
from dagster_polars.types import LazyFrameWithMetadata, StorageMetadata

if TYPE_CHECKING:
    import fsspec


def get_pyarrow_dataset(path: UPath, context: InputContext) -> pyarrow.dataset.Dataset:
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


def scan_parquet_legacy(path: UPath, context: InputContext) -> pl.LazyFrame:
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


def scan_parquet(path: UPath, context: InputContext) -> pl.LazyFrame:
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


class PolarsParquetIOManager(BasePolarsUPathIOManager):
    extension: str = ".parquet"
    use_legacy_reader: bool = False

    assert BasePolarsUPathIOManager.__doc__ is not None
    __doc__ = (
        BasePolarsUPathIOManager.__doc__
        + """\nWorks with Parquet files.
    All read/write arguments can be passed via corresponding metadata values."""
    )

    def dump_df_to_path(
        self,
        context: OutputContext,
        df: pl.DataFrame,
        path: UPath,
        metadata: Optional[StorageMetadata] = None,
    ):
        assert context.metadata is not None

        table: Table = df.to_arrow()

        if metadata is not None:
            existing_metadata = (
                table.schema.metadata.to_dict() if table.schema.metadata is not None else {}
            )
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

    def scan_df_from_path(
        self, path: UPath, context: InputContext, with_metadata: Optional[bool] = False
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

            metadata = (
                json.loads(dagster_polars_metadata) if dagster_polars_metadata is not None else {}
            )

            return ldf, metadata

    @classmethod
    def read_parquet_metadata(cls, path: UPath) -> StorageMetadata:
        """Just a helper method to read metadata from a parquet file.

        Is actually not used internally.
        :param path:
        :return:
        """
        metadata = pyarrow.parquet.read_metadata(
            str(path), filesystem=path.fs if hasattr(path, "fs") else None
        ).metadata

        dagster_polars_metadata = (
            metadata.get(DAGSTER_POLARS_STORAGE_METADATA_KEY.encode("utf-8"))
            if metadata is not None
            else None
        )

        return json.loads(dagster_polars_metadata) if dagster_polars_metadata is not None else {}
