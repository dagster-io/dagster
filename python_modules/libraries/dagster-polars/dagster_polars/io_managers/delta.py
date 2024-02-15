import json
from enum import Enum
from pprint import pformat
from typing import TYPE_CHECKING, Any, Dict, Literal, Optional, Union, overload

import dagster._check as check
import polars as pl
from dagster import InputContext, MetadataValue, OutputContext
from dagster._annotations import experimental
from dagster._core.storage.upath_io_manager import is_dict_type

from dagster_polars.io_managers.base import BasePolarsUPathIOManager
from dagster_polars.types import DataFrameWithMetadata, LazyFrameWithMetadata, StorageMetadata

try:
    from deltalake import DeltaTable
    from deltalake.exceptions import TableNotFoundError
except ImportError as e:
    raise ImportError("Install 'dagster-polars[deltalake]' to use DeltaLake functionality") from e

if TYPE_CHECKING:
    from upath import UPath


DAGSTER_POLARS_STORAGE_METADATA_SUBDIR = ".dagster_polars_metadata"

SINGLE_LOADING_TYPES = (pl.DataFrame, pl.LazyFrame, LazyFrameWithMetadata, DataFrameWithMetadata)


class DeltaWriteMode(str, Enum):
    error = "error"
    append = "append"
    overwrite = "overwrite"
    ignore = "ignore"


@experimental
class PolarsDeltaIOManager(BasePolarsUPathIOManager):
    """Implements writing and reading DeltaLake tables.

    Features:
     - All features provided by :py:class:`~dagster_polars.BasePolarsUPathIOManager`.
     - All read/write options can be set via corresponding metadata or config parameters (metadata takes precedence).
     - Supports native DeltaLake partitioning by storing different asset partitions in the same DeltaLake table.
       To enable this behavior, set the `partition_by` metadata value or config parameter (it's passed to `delta_write_options` of `pl.DataFrame.write_delta`).
       Automatically filters loaded partitions, unless `MultiPartitionsDefinition` is used.
       With `MultiPartitionsDefinition` you are responsible for filtering the partitions in the downstream asset, as it's non-trivial to do so in the IOManager.
       When loading all available asset partitions, the whole table can be loaded in one go by using type annotations like `pl.DataFrame` and `pl.LazyFrame`.
     - Supports writing/reading custom metadata to/from `.dagster_polars_metadata/<version>.json` file in the DeltaLake table directory.

    Install `dagster-polars[delta]` to use this IOManager.

    Examples:
        .. code-block:: python

            from dagster import asset
            from dagster_polars import PolarsDeltaIOManager
            import polars as pl

            @asset(
                io_manager_key="polars_delta_io_manager",
                key_prefix=["my_dataset"]
            )
            def my_asset() -> pl.DataFrame:  # data will be stored at <base_dir>/my_dataset/my_asset.delta
                ...

            defs = Definitions(
                assets=[my_table],
                resources={
                    "polars_parquet_io_manager": PolarsDeltaIOManager(base_dir="s3://my-bucket/my-dir")
                }
            )


        Appending to a DeltaLake table:

        .. code-block:: python

            @asset(
                io_manager_key="polars_delta_io_manager",
                metadata={
                    "mode": "append"
                },
            )
            def my_table() -> pl.DataFrame:
                ...

        Using native DeltaLake partitioning by storing different asset partitions in the same DeltaLake table:

        .. code-block:: python

            from dagster import AssetExecutionContext, DailyPartitionedDefinition
            from dagster_polars import LazyFramePartitions

            @asset(
                io_manager_key="polars_delta_io_manager",
                metadata={
                    "partition_by": "partition_col"
                },
                partitions_def=...
            )
            def upstream(context: AssetExecutionContext) -> pl.DataFrame:
                df = ...

                # add partition to the DataFrame
                df = df.with_columns(pl.lit(context.partition_key).alias("partition_col"))
                return df

            @asset
            def downstream(upstream: LazyFramePartitions) -> pl.DataFrame:
                # concat LazyFrames, filter required partitions and call .collect()
                ...
    """

    extension: str = ".delta"
    mode: DeltaWriteMode = DeltaWriteMode.overwrite.value  # type: ignore
    overwrite_schema: bool = False
    version: Optional[int] = None

    # tmp fix until UPathIOManager supports this: added special handling for loading all partitions of an asset

    def load_input(self, context: InputContext) -> Union[Any, Dict[str, Any]]:
        # If no asset key, we are dealing with an op output which is always non-partitioned
        if not context.has_asset_key or not context.has_asset_partitions:
            path = self._get_path(context)
            return self._load_single_input(path, context)
        else:
            asset_partition_keys = context.asset_partition_keys
            if len(asset_partition_keys) == 0:
                return None
            elif len(asset_partition_keys) == 1:
                paths = self._get_paths_for_partitions(context)
                check.invariant(len(paths) == 1, f"Expected 1 path, but got {len(paths)}")
                path = next(iter(paths.values()))
                backcompat_paths = self._get_multipartition_backcompat_paths(context)
                backcompat_path = (
                    None if not backcompat_paths else next(iter(backcompat_paths.values()))
                )

                return self._load_partition_from_path(
                    context=context,
                    partition_key=asset_partition_keys[0],
                    path=path,
                    backcompat_path=backcompat_path,
                )
            else:  # we are dealing with multiple partitions of an asset
                type_annotation = context.dagster_type.typing_type
                if type_annotation == Any or is_dict_type(type_annotation):
                    return self._load_multiple_inputs(context)

                # special case of loading the whole DeltaLake table at once
                # when using AllPartitionMappings and native DeltaLake partitioning
                elif (
                    context.upstream_output is not None
                    and context.upstream_output.metadata is not None
                    and context.upstream_output.metadata.get("partition_by") is not None
                    and type_annotation in SINGLE_LOADING_TYPES
                    and context.upstream_output.asset_info is not None
                    and context.upstream_output.asset_info.partitions_def is not None
                    and set(asset_partition_keys)
                    == set(
                        context.upstream_output.asset_info.partitions_def.get_partition_keys(
                            dynamic_partitions_store=context.instance
                        )
                    )
                ):
                    # load all partitions at once
                    return self.load_from_path(
                        context=context,
                        path=self.get_path_for_partition(
                            context=context,
                            partition=asset_partition_keys[0],  # 0 would work,
                            path=self._get_paths_for_partitions(context)[
                                asset_partition_keys[0]
                            ],  # 0 would work,
                        ),
                        partition_key=None,
                    )
                else:
                    check.failed(
                        "Loading an input that corresponds to multiple partitions, but the"
                        f" type annotation on the op input is not a dict, Dict, Mapping, one of {SINGLE_LOADING_TYPES},"
                        " or Any: is '{type_annotation}'."
                    )

    def sink_df_to_path(
        self,
        context: OutputContext,
        df: pl.LazyFrame,
        path: "UPath",
        metadata: Optional[StorageMetadata] = None,
    ):
        context_metadata = context.metadata or {}
        streaming = context_metadata.get("streaming", False)
        return self.write_df_to_path(context, df.collect(streaming=streaming), path, metadata)

    def write_df_to_path(
        self,
        context: OutputContext,
        df: pl.DataFrame,
        path: "UPath",
        metadata: Optional[StorageMetadata] = None,  # why is metadata passed
    ):
        context_metadata = context.metadata or {}
        delta_write_options = context_metadata.get(
            "delta_write_options"
        )  # This needs to be gone and just only key value on the metadata

        if context.has_asset_partitions:
            delta_write_options = delta_write_options or {}
            partition_by = context_metadata.get(
                "partition_by"
            )  # this could be wrong, you could have partition_by in delta_write_options and in the metadata

            if partition_by is not None:
                assert (
                    context.partition_key is not None
                ), 'can\'t set "partition_by" for an asset without partitions'

                delta_write_options["partition_by"] = partition_by
                delta_write_options["partition_filters"] = [
                    (partition_by, "=", context.partition_key)
                ]

        if delta_write_options is not None:
            context.log.debug(f"Writing with delta_write_options: {pformat(delta_write_options)}")

        storage_options = self.storage_options
        try:
            dt = DeltaTable(str(path), storage_options=storage_options)
        except TableNotFoundError:
            dt = str(path)

        df.write_delta(
            dt,
            mode=context_metadata.get("mode") or self.mode.value,
            overwrite_schema=context_metadata.get("overwrite_schema") or self.overwrite_schema,
            storage_options=storage_options,
            delta_write_options=delta_write_options,
        )
        if isinstance(dt, DeltaTable):
            current_version = dt.version()
        else:
            current_version = DeltaTable(
                str(path), storage_options=storage_options, without_files=True
            ).version()
        context.add_output_metadata({"version": current_version})

        if metadata is not None:
            metadata_path = self.get_storage_metadata_path(path, current_version)
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            metadata_path.write_text(json.dumps(metadata))

    @overload
    def scan_df_from_path(
        self, path: "UPath", context: InputContext, with_metadata: Literal[None, False]
    ) -> pl.LazyFrame:
        ...

    @overload
    def scan_df_from_path(
        self, path: "UPath", context: InputContext, with_metadata: Literal[True]
    ) -> LazyFrameWithMetadata:
        ...

    def scan_df_from_path(
        self,
        path: "UPath",
        context: InputContext,
        with_metadata: Optional[bool] = False,
    ) -> Union[pl.LazyFrame, LazyFrameWithMetadata]:
        context_metadata = context.metadata or {}

        version = self.get_delta_version_to_load(path, context)

        context.log.debug(f"Reading Delta table with version: {version}")

        ldf = pl.scan_delta(
            str(path),
            version=version,
            delta_table_options=context_metadata.get("delta_table_options"),
            pyarrow_options=context_metadata.get("pyarrow_options"),
            storage_options=self.storage_options,
        )

        if with_metadata:
            version = self.get_delta_version_to_load(path, context)
            metadata_path = self.get_storage_metadata_path(path, version)
            if metadata_path.exists():
                metadata = json.loads(metadata_path.read_text())
            else:
                metadata = {}
            return ldf, metadata

        else:
            return ldf

    def get_path_for_partition(
        self, context: Union[InputContext, OutputContext], path: "UPath", partition: str
    ) -> "UPath":
        if isinstance(context, InputContext):
            if (
                context.upstream_output is not None
                and context.upstream_output.metadata is not None
                and context.upstream_output.metadata.get("partition_by") is not None
            ):
                # upstream asset has "partition_by" metadata set, so partitioning for it is handled by DeltaLake itself
                return path

        if isinstance(context, OutputContext):
            if context.metadata is not None and context.metadata.get("partition_by") is not None:
                # this asset has "partition_by" metadata set, so partitioning for it is handled by DeltaLake itself
                return path

        return path / partition  # partitioning is handled by the IOManager

    def get_metadata(
        self, context: OutputContext, obj: Union[pl.DataFrame, pl.LazyFrame, None]
    ) -> Dict[str, MetadataValue]:
        context_metadata = context.metadata or {}

        metadata = super().get_metadata(context, obj)

        if context.has_asset_partitions:
            partition_by = context_metadata.get("partition_by")
            if partition_by is not None:
                metadata["partition_by"] = partition_by

        if context_metadata.get("mode") == "append":
            # modify the medatata to reflect the fact that we are appending to the table

            if context.has_asset_partitions:
                # paths = self._get_paths_for_partitions(context)
                # assert len(paths) == 1
                # path = list(paths.values())[0]

                # FIXME: what to about row_count metadata do if we are appending to a partitioned table?
                # we should not be using the full table length,
                # but it's unclear how to get the length of the partition we are appending to
                pass
            else:
                metadata["append_row_count"] = metadata["row_count"]

                path = self._get_path(context)
                # we need to get row_count from the full table
                metadata["row_count"] = MetadataValue.int(
                    DeltaTable(str(path), storage_options=self.storage_options)
                    .to_pyarrow_dataset()
                    .count_rows()
                )

        return metadata

    def get_delta_version_to_load(self, path: "UPath", context: InputContext) -> int:
        context_metadata = context.metadata or {}
        version_from_metadata = context_metadata.get("version")

        version_from_config = self.version

        version: Optional[int] = None

        if version_from_metadata is not None and version_from_config is not None:
            context.log.warning(
                f"Both version from metadata ({version_from_metadata}) "
                f"and config ({version_from_config}) are set. Using version from metadata."
            )
            version = int(version_from_metadata)
        elif version_from_metadata is None and version_from_config is not None:
            version = int(version_from_config)
        elif version_from_metadata is not None and version_from_config is None:
            version = int(version_from_metadata)

        if version is None:
            return DeltaTable(
                str(path), storage_options=self.storage_options, without_files=True
            ).version()
        else:
            return version

    def get_storage_metadata_path(self, path: "UPath", version: int) -> "UPath":
        return path / DAGSTER_POLARS_STORAGE_METADATA_SUBDIR / f"{version}.json"
