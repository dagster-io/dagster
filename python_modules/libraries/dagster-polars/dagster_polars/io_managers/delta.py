from collections import defaultdict
from collections.abc import Mapping, Sequence
from enum import Enum
from pprint import pformat
from typing import TYPE_CHECKING, Any, Optional, Union

import packaging.version
import polars as pl
from dagster import InputContext, MetadataValue, MultiPartitionKey, OutputContext
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.storage.upath_io_manager import is_dict_type

from dagster_polars.io_managers.base import BasePolarsUPathIOManager

try:
    from deltalake import DeltaTable
    from deltalake.exceptions import TableNotFoundError
except ImportError as e:
    if "deltalake" in str(e):
        raise ImportError(
            "Install 'dagster-polars[deltalake]' to use DeltaLake functionality"
        ) from e
    else:
        raise e

if TYPE_CHECKING:
    from upath import UPath


SINGLE_LOADING_TYPES = (pl.DataFrame, pl.LazyFrame)


class DeltaWriteMode(str, Enum):
    error = "error"
    append = "append"
    overwrite = "overwrite"
    ignore = "ignore"


class PolarsDeltaIOManager(BasePolarsUPathIOManager):
    """Implements writing and reading DeltaLake tables.

    Features:
     - All features provided by :py:class:`~dagster_polars.BasePolarsUPathIOManager`.
     - All read/write options can be set via corresponding metadata or config parameters (metadata takes precedence).
     - Supports native DeltaLake partitioning by storing different asset partitions in the same DeltaLake table.
       To enable this behavior, set the `partition_by` metadata value or config parameter **and** use a non-dict type annotation when loading the asset.
       The `partition_by` value will be used in `delta_write_options` of `pl.DataFrame.write_delta` and `pyarrow_options` of `pl.scan_delta`).
       When using a one-dimensional `PartitionsDefinition`, it should be a single string like `"column"`. When using a `MultiPartitionsDefinition`,
       it should be a dict with dimension to column names mapping, like `{"dimension": "column"}`.

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
                partitions_def=StaticPartitionsDefinition(["a, "b", "c"])
            )
            def upstream(context: AssetExecutionContext) -> pl.DataFrame:
                df = ...

                # column with the partition_key must match `partition_by` metadata value
                return df.with_columns(pl.lit(context.partition_key).alias("partition_col"))

            @asset
            def downstream(upstream: pl.LazyFrame) -> pl.DataFrame:
                ...

        When using `MuiltiPartitionsDefinition`, `partition_by` metadata value should be a dictionary mapping dimensions to column names.

        .. code-block:: python

            from dagster import AssetExecutionContext, DailyPartitionedDefinition, MultiPartitionsDefinition, StaticPartitionsDefinition
            from dagster_polars import LazyFramePartitions

            @asset(
                io_manager_key="polars_delta_io_manager",
                metadata={
                    "partition_by": {"time": "date", "clients": "client"}  # dimension -> column mapping
                },
                partitions_def=MultiPartitionsDefinition(
                    {
                        "date": DailyPartitionedDefinition(...),
                        "clients": StaticPartitionsDefinition(...)
                    }
                )
            )
            def upstream(context: AssetExecutionContext) -> pl.DataFrame:
                df = ...

                partition_keys_by_dimension = context.partition_key.keys_by_dimension

                return df.with_columns(
                    pl.lit(partition_keys_by_dimension["time"]).alias("date"),  # time dimension matches date column
                    pl.lit(partition_keys_by_dimension["clients"]).alias("client")  # clients dimension matches client column
                )


            @asset
            def downstream(upstream: pl.LazyFrame) -> pl.DataFrame:
                ...

    """

    extension: str = ".delta"  # pyright: ignore[reportIncompatibleVariableOverride]
    mode: DeltaWriteMode = DeltaWriteMode.overwrite.value  # type: ignore
    overwrite_schema: bool = False
    version: Optional[int] = None

    def sink_df_to_path(
        self,
        context: OutputContext,
        df: pl.LazyFrame,
        path: "UPath",
    ):
        context_metadata = context.definition_metadata or {}
        streaming = context_metadata.get("streaming", False)

        # workaround for bug introduced in polars 1.25.2 where streaming=False stopped working
        if streaming:
            return self.write_df_to_path(context, df.collect(streaming=True), path)  # type: ignore
        else:
            return self.write_df_to_path(context, df.collect(), path)

    def write_df_to_path(
        self,
        context: OutputContext,
        df: pl.DataFrame,
        path: "UPath",
    ):
        context_metadata = context.definition_metadata or {}
        delta_write_options = context_metadata.get(
            "delta_write_options"
        )  # This needs to be gone and just only key value on the metadata

        if context.has_asset_partitions:
            delta_write_options = delta_write_options or {}
            # this could be wrong, you could have partition_by in
            # delta_write_options and in the metadata
            partition_by = context_metadata.get("partition_by")

            if partition_by is not None:
                assert (
                    context.partition_key is not None
                ), "Cannot set `partition_by` for an asset without partitions."

                if isinstance(partition_by, dict) and isinstance(
                    context.partition_key, MultiPartitionKey
                ):
                    delta_write_options["partition_by"] = list(partition_by.values())
                elif isinstance(partition_by, str) and isinstance(context.partition_key, str):
                    delta_write_options["partition_by"] = partition_by
                else:
                    raise ValueError(
                        "Metadata value for `partition_by` must be a string "
                        "for single-partitioned assets or a dictionary for "
                        "multi-partitioned assets.\n"
                        f"Found: `{partition_by}`"
                    )

                # rust is the default engine in newer versions of deltalake
                if (engine := delta_write_options.get("engine", "rust")) == "rust":
                    delta_write_options["predicate"] = self.get_predicate(context)

                elif engine == "pyarrow":
                    delta_write_options["partition_filters"] = self.get_partition_filters(context)

                else:
                    raise NotImplementedError(f"Invalid engine: {engine}")

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

    def scan_df_from_path(
        self,
        path: "UPath",
        context: InputContext,
    ) -> pl.LazyFrame:
        """This method scans a DeltaLake table into a `polars.LazyFrame`.
        It can be called in 3 different situations:
        1. with an unpartitioned asset
        2. with a partitioned asset without native partitioning enabled -
           multiple times on nested .delta tables
        3. with a partitioned asset and with native partitioning enabled - a
           single time on the .delta table.

        In the (3) option we apply partition filters to only load mapped partitions
        """
        assert context.upstream_output is not None
        assert context.upstream_output.definition_metadata is not None

        context_metadata = context.definition_metadata or {}

        version = self.get_delta_version_to_load(path, context)

        context.log.debug(f"Reading Delta table with version: {version}")

        pyarrow_options = context_metadata.get("pyarrow_options", {})

        partition_by = context.upstream_output.definition_metadata.get("partition_by")

        # we want to apply partition filters when loading some partitions, but
        # not all partitions
        if (
            partition_by
            and len(context.asset_partition_keys) > 0
            and context.has_asset_key is not None
            and context.has_asset_partitions is not None
            and context.asset_partition_keys
            != set(
                context.upstream_output.asset_partitions_def.get_partition_keys(
                    dynamic_partitions_store=context.instance
                )
            )
        ):
            pyarrow_options["partitions"] = self.get_partition_filters(context)

        if pyarrow_options:
            context.log.debug(f"Reading with pyarrow_options: {pyarrow_options}")

        delta_table_options = context_metadata.get("delta_table_options")

        if delta_table_options:
            context.log.debug(f"Reading with delta_table_options: {delta_table_options}")

        return pl.scan_delta(
            str(path),
            version=version,
            delta_table_options=delta_table_options,
            storage_options=self.storage_options,
            **_get_pyarrow_options_kwargs(pyarrow_options),
        )

    def load_partitions(self, context: InputContext):
        assert context.upstream_output is not None
        # any partition would work as they all are stored in the same DeltaLake
        # table
        path = self._get_path_without_extension(context)
        context.log.debug(
            f"Loading {len(context.asset_partition_keys)} partitions from {path} using {self.__class__.__name__}..."
        )
        if context.upstream_output.definition_metadata.get("partition_by") and not is_dict_type(
            context.dagster_type.typing_type
        ):
            # user enabled native partitioning and wants a `pl.DataFrame` or
            # `pl.LazyFrame`
            return self.load_from_path(context, self._with_extension(path))
        else:
            # default behaviour
            return super().load_partitions(context)

    def get_path_for_partition(
        self, context: Union[InputContext, OutputContext], path: "UPath", partition: str
    ) -> "UPath":
        if isinstance(context, InputContext):
            if (
                context.upstream_output is not None
                and context.upstream_output.definition_metadata is not None
                and context.upstream_output.definition_metadata.get("partition_by") is not None
            ):
                # upstream asset has "partition_by" metadata set, so
                # partitioning for it is handled by DeltaLake itself
                return path

        if isinstance(context, OutputContext):
            if (
                context.definition_metadata is not None
                and context.definition_metadata.get("partition_by") is not None
            ):
                # this asset has "partition_by" metadata set, so partitioning
                # for it is handled by DeltaLake itself
                return path

        return path / partition  # partitioning is handled by the IOManager

    @staticmethod
    def get_partition_filters(
        context: Union[InputContext, OutputContext],
    ) -> Sequence[tuple[str, str, Any]]:
        """Create filters for `deltalake` to know which partitions are overwritten.

        Only used with the PyArrow, which will be removed in `deltalake>=1`.
        """
        if isinstance(context, OutputContext):
            partition_by = context.definition_metadata.get("partition_by")
        elif isinstance(context, InputContext) and context.upstream_output is not None:
            partition_by = context.upstream_output.definition_metadata.get("partition_by")
        else:
            raise DagsterInvariantViolationError(f"Invalid context type: {type(context)}")

        if partition_by is None or not context.has_asset_partitions:
            filters = []
        elif isinstance(partition_by, dict):
            all_keys_by_dim = defaultdict(list)
            for partition_key in context.asset_partition_keys:
                assert isinstance(partition_key, MultiPartitionKey), (
                    f"Received dict `partition_by` metadata value {partition_by}, "
                    f"but the partition_key is not a `MultiPartitionKey`: {partition_key}"
                )
                for dim, key in partition_key.keys_by_dimension.items():
                    all_keys_by_dim[dim].append(key)

            filters = [(partition_by[dim], "in", keys) for dim, keys in all_keys_by_dim.items()]

        elif isinstance(partition_by, str):
            assert not isinstance(context.asset_partition_keys[0], MultiPartitionKey), (
                f"Received string `partition_by` metadata value `{partition_by}`, "
                f"but the partition_key is not a `MultiPartitionKey`: {context.asset_partition_keys[0]}"
            )
            filters = [(partition_by, "in", context.asset_partition_keys)]

        else:
            raise NotImplementedError(f"Unsupported `partition_by` metadata value: {partition_by}")

        return filters

    @staticmethod
    def get_predicate(
        context: Union[InputContext, OutputContext],
    ) -> Optional[str]:
        """Create a predicate for `deltalake` to select which partitions are overwritten.

        Returns `None` if the entire table is overwritten.

        See documentation here:
        https://delta-io.github.io/delta-rs/usage/writing/#overwriting-part-of-the-table-data-using-a-predicate
        """
        if isinstance(context, OutputContext):
            partition_by = context.definition_metadata.get("partition_by")
        elif isinstance(context, InputContext) and context.upstream_output is not None:
            partition_by = context.upstream_output.definition_metadata.get("partition_by")
        else:
            raise DagsterInvariantViolationError(f"Invalid context type: {type(context)}")

        def key_to_predicate(key):
            return f"'{key}'"

        if partition_by is None or not context.has_asset_partitions:
            return

        elif isinstance(partition_by, dict):
            all_keys_by_dim = defaultdict(list)
            for partition_key in context.asset_partition_keys:
                assert isinstance(partition_key, MultiPartitionKey), (
                    f"Received dict `partition_by` metadata value `{partition_by}`, "
                    f"but the partition_key is not a `MultiPartitionKey`: `{partition_key}`."
                )
                for dim, key in partition_key.keys_by_dimension.items():
                    all_keys_by_dim[dim].append(key)

            predicate = " AND ".join(
                [
                    f"{partition_by[dim]} in ({', '.join(map(key_to_predicate,  keys))})"
                    for dim, keys in all_keys_by_dim.items()
                ]
            )

        elif isinstance(partition_by, str):
            assert not isinstance(context.asset_partition_keys[0], MultiPartitionKey), (
                f"Received string `partition_by` metadata value `{partition_by}`, "
                f"but the partition_key is not a `MultiPartitionKey`: {context.asset_partition_keys[0]}"
            )

            if len(context.asset_partition_keys) == 1:
                predicate = f"{partition_by} = '{context.asset_partition_keys[0]}'"
            else:
                predicate = f"{partition_by} in ({', '.join(map(key_to_predicate, context.asset_partition_keys))})"

        else:
            raise NotImplementedError(f"Unsupported `partition_by` metadata value: {partition_by}")

        return predicate

    def get_metadata(
        self, context: OutputContext, obj: Union[pl.DataFrame, pl.LazyFrame, None]
    ) -> dict[str, MetadataValue]:
        context_metadata = context.definition_metadata or {}

        metadata = super().get_metadata(context, obj)

        if context.has_asset_partitions:
            partition_by = context_metadata.get("partition_by")
            if partition_by is not None:
                metadata["partition_by"] = partition_by

        if context_metadata.get("mode") == "append":
            # modify the metadata to reflect the fact that we are appending to
            # the table

            if context.has_asset_partitions:
                # paths = self._get_paths_for_partitions(context)
                # assert len(paths) == 1
                # path = list(paths.values())[0]

                # FIXME: what to about row_count metadata do if we are
                # appending to a partitioned table?
                # we should not be using the full table length,
                # but it's unclear how to get the length of the partition we
                # are appending to
                pass
            else:
                metadata["append_row_count"] = metadata["dagster/row_count"]

                path = self._get_path(context)
                # we need to get row_count from the full table
                metadata["dagster/row_count"] = MetadataValue.int(
                    DeltaTable(str(path), storage_options=self.storage_options)
                    .to_pyarrow_dataset()
                    .count_rows()
                )

        return metadata

    def get_delta_version_to_load(self, path: "UPath", context: InputContext) -> int:
        context_metadata = context.definition_metadata or {}
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


# polars>=1.14.0 requires use_pyarrow=True when setting pyarrow_options
def _get_pyarrow_options_kwargs(pyarrow_options: Mapping[str, object]) -> Mapping[str, Any]:
    kwargs: dict[str, object] = {"pyarrow_options": pyarrow_options}
    if packaging.version.parse(pl.__version__) >= packaging.version.parse("1.14.0"):
        kwargs["use_pyarrow"] = True
    return kwargs
