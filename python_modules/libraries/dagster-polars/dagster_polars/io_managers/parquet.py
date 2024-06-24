from typing import TYPE_CHECKING, Any, Dict, Optional, Union, cast

import polars as pl
import pyarrow.dataset as ds
from dagster import InputContext, OutputContext
from dagster._annotations import experimental
from fsspec.implementations.local import LocalFileSystem
from packaging.version import Version

from dagster_polars.io_managers.base import BasePolarsUPathIOManager

if TYPE_CHECKING:
    from upath import UPath


DAGSTER_POLARS_STORAGE_METADATA_KEY = "dagster_polars_metadata"


def get_pyarrow_dataset(path: "UPath", context: InputContext) -> ds.Dataset:
    context_metadata = context.definition_metadata or {}

    fs = path.fs if hasattr(path, "fs") else None

    if context_metadata.get("partitioning") is not None:
        context.log.warning(
            f'"partitioning" metadata value for PolarsParquetIOManager is deprecated '
            f'in favor of "partition_by" (loading from {path})'
        )

    dataset = ds.dataset(
        str(path),
        filesystem=fs,
        format=context_metadata.get("format", "parquet"),
        partitioning=context_metadata.get("partitioning") or context_metadata.get("partition_by"),
        partition_base_dir=context_metadata.get("partition_base_dir"),
        exclude_invalid_files=context_metadata.get("exclude_invalid_files", True),
        ignore_prefixes=context_metadata.get("ignore_prefixes", [".", "_"]),
    )

    return dataset


def scan_parquet(path: "UPath", context: InputContext) -> pl.LazyFrame:
    """Scan a parquet file and return a lazy frame (uses polars native reader).

    :param path:
    :param context:
    :return:
    """
    context_metadata = context.definition_metadata or {}

    storage_options = cast(
        Optional[Dict[str, Any]],
        (path.storage_options if hasattr(path, "storage_options") else None),
    )

    kwargs = dict(
        n_rows=context_metadata.get("n_rows", None),
        cache=context_metadata.get("cache", True),
        parallel=context_metadata.get("parallel", "auto"),
        rechunk=context_metadata.get("rechunk", True),
        low_memory=context_metadata.get("low_memory", False),
        use_statistics=context_metadata.get("use_statistics", True),
        hive_partitioning=context_metadata.get("hive_partitioning", True),
        retries=context_metadata.get("retries", 0),
    )
    if Version(pl.__version__) >= Version("0.20.4"):
        kwargs["row_index_name"] = context_metadata.get("row_index_name", None)
        kwargs["row_index_offset"] = context_metadata.get("row_index_offset", 0)
    else:
        kwargs["row_count_name"] = context_metadata.get("row_count_name", None)
        kwargs["row_count_offset"] = context_metadata.get("row_count_offset", 0)

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
                    "partition_by": ["year", "month", "day"]
                }
            )

    """

    extension: str = ".parquet"

    def sink_df_to_path(
        self,
        context: OutputContext,
        df: pl.LazyFrame,
        path: "UPath",
    ):
        context_metadata = context.definition_metadata or {}

        fs = path.fs if hasattr(path, "fs") else None
        if isinstance(fs, LocalFileSystem):
            compression = context_metadata.get("compression", "zstd")
            compression_level = context_metadata.get("compression_level")
            statistics = context_metadata.get("statistics", False)
            row_group_size = context_metadata.get("row_group_size")

            df.sink_parquet(
                str(path),
                compression=compression,
                compression_level=compression_level,
                statistics=statistics,
                row_group_size=row_group_size,
            )
        else:
            # TODO(ion): add sink_parquet once this PR gets merged: https://github.com/pola-rs/polars/pull/11519
            context.log.warning(
                "Cloud sink is not possible yet, instead it's dispatched to pyarrow writer which collects it into memory first.",
            )
            return self.write_df_to_path(context, df.collect(), path)

    def write_df_to_path(
        self,
        context: OutputContext,
        df: pl.DataFrame,
        path: "UPath",
    ):
        context_metadata = context.definition_metadata or {}
        compression = context_metadata.get("compression", "zstd")
        compression_level = context_metadata.get("compression_level")
        statistics = context_metadata.get("statistics", False)
        row_group_size = context_metadata.get("row_group_size")
        pyarrow_options = context_metadata.get("pyarrow_options", None)

        fs = path.fs if hasattr(path, "fs") else None

        if pyarrow_options is not None:
            pyarrow_options["filesystem"] = fs
            df.write_parquet(
                str(path),
                compression=compression,  # type: ignore
                compression_level=compression_level,
                statistics=statistics,
                row_group_size=row_group_size,
                use_pyarrow=True,
                pyarrow_options=pyarrow_options,
            )
        elif fs is not None:
            with fs.open(str(path), mode="wb") as f:
                df.write_parquet(
                    f,
                    compression=compression,  # type: ignore
                    compression_level=compression_level,
                    statistics=statistics,
                    row_group_size=row_group_size,
                )
        else:
            df.write_parquet(
                str(path),
                compression=compression,  # type: ignore
                compression_level=compression_level,
                statistics=statistics,
                row_group_size=row_group_size,
            )

    def scan_df_from_path(
        self,
        path: "UPath",
        context: InputContext,
        partition_key: Optional[str] = None,
    ) -> Union[pl.LazyFrame]:
        return scan_parquet(path, context)
