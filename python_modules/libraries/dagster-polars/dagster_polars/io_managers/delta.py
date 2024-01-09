import json
from enum import Enum
from pprint import pformat
from typing import Dict, Optional, Union

import polars as pl
from dagster import InputContext, MetadataValue, OutputContext
from dagster._annotations import experimental

from dagster_polars.types import LazyFrameWithMetadata, StorageMetadata

try:
    from deltalake import DeltaTable
except ImportError as e:
    raise ImportError("Install 'dagster-polars[deltalake]' to use DeltaLake functionality") from e
from upath import UPath

from dagster_polars.io_managers.base import BasePolarsUPathIOManager

DAGSTER_POLARS_STORAGE_METADATA_SUBDIR = ".dagster_polars_metadata"


class DeltaWriteMode(str, Enum):
    error = "error"
    append = "append"
    overwrite = "overwrite"
    ignore = "ignore"


@experimental
class PolarsDeltaIOManager(BasePolarsUPathIOManager):
    """Implements writing and reading DeltaLake tables.
    
    Features:
     - All features provided by :py:class:`~dagster_polars.io_managers.base.BasePolarsUPathIOManager`.
     - All read/write options can be set via corresponding metadata or config parameters (metadata takes preference).
     - Supports native DeltaLake partitioning by storing different asset partitions in the same DeltaLake table. To enable this behavior, set the `partition_by` metadata value or config parameter (it's passed to `delta_write_options` of `pl.DataFrame.write_delta`). When using native DeltaLake partitioning, you are responsible for filtering correct partitions when reading the data in downstream assets.
     - Supports writing/reading custom metadata to/from `.dagster_polars_metadata/<version>.json` file in the DeltaLake table directory.
     
    Install `dagster-polars[delta]` to use this IOManager.

    Examples
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

    """

    extension: str = ".delta"
    mode: DeltaWriteMode = DeltaWriteMode.overwrite.value  # type: ignore
    overwrite_schema: bool = False
    version: Optional[int] = None

    def dump_df_to_path(
        self,
        context: OutputContext,
        df: pl.DataFrame,
        path: UPath,
        metadata: Optional[StorageMetadata] = None,
    ):
        assert context.metadata is not None

        delta_write_options = context.metadata.get("delta_write_options")

        if context.has_asset_partitions:
            delta_write_options = delta_write_options or {}
            partition_by = context.metadata.get("partition_by")

            if partition_by is not None:
                delta_write_options["partition_by"] = partition_by

        if delta_write_options is not None:
            context.log.debug(f"Writing with delta_write_options: {pformat(delta_write_options)}")

        storage_options = self.get_storage_options(path)

        df.write_delta(
            str(path),
            mode=context.metadata.get("mode") or self.mode,  # type: ignore
            overwrite_schema=context.metadata.get("overwrite_schema") or self.overwrite_schema,
            storage_options=storage_options,
            delta_write_options=delta_write_options,
        )
        current_version = DeltaTable(str(path), storage_options=storage_options).version()
        context.add_output_metadata({"version": current_version})

        if metadata is not None:
            metadata_path = self.get_storage_metadata_path(path, current_version)
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            metadata_path.write_text(json.dumps(metadata))

    def scan_df_from_path(
        self, path: UPath, context: InputContext, with_metadata: bool = False
    ) -> Union[pl.LazyFrame, LazyFrameWithMetadata]:
        assert context.metadata is not None

        version = self.get_delta_version_to_load(path, context)

        context.log.debug(f"Reading Delta table with version: {version}")

        ldf = pl.scan_delta(
            str(path),
            version=version,
            delta_table_options=context.metadata.get("delta_table_options"),
            pyarrow_options=context.metadata.get("pyarrow_options"),
            storage_options=self.get_storage_options(path),
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
        self, context: Union[InputContext, OutputContext], path: UPath, partition: str
    ) -> UPath:
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

    def get_metadata(self, context: OutputContext, obj: pl.DataFrame) -> Dict[str, MetadataValue]:
        assert context.metadata is not None

        metadata = super().get_metadata(context, obj)

        if context.has_asset_partitions:
            partition_by = context.metadata.get("partition_by")
            if partition_by is not None:
                metadata["partition_by"] = partition_by

        if context.metadata.get("mode") == "append":
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
                    DeltaTable(str(path), storage_options=self.get_storage_options(path))
                    .to_pyarrow_dataset()
                    .count_rows()
                )

        return metadata

    def get_delta_version_to_load(self, path: UPath, context: InputContext) -> int:
        assert context.metadata is not None
        version_from_metadata = context.metadata.get("version")

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

        version = DeltaTable(
            str(path),
            storage_options=self.get_storage_options(path),
            version=version,
        ).version()

        assert version is not None, "DeltaTable version is None. This should not happen."
        return version

    def get_storage_metadata_path(self, path: UPath, version: int) -> UPath:
        return path / DAGSTER_POLARS_STORAGE_METADATA_SUBDIR / f"{version}.json"
