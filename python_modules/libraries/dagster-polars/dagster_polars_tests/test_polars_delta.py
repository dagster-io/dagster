from datetime import datetime

import polars as pl
import polars.testing as pl_testing
from dagster import (
    AssetExecutionContext,
    AssetIn,
    Config,
    DagsterInstance,
    DailyPartitionsDefinition,
    MultiPartitionKey,
    MultiPartitionsDefinition,
    OpExecutionContext,
    RunConfig,
    StaticPartitionsDefinition,
    asset,
    materialize,
)
from dagster_polars import PolarsDeltaIOManager
from dagster_polars.io_managers.delta import DeltaWriteMode
from deltalake import DeltaTable

from dagster_polars_tests.utils import get_saved_path


def test_polars_delta_io_manager_append(polars_delta_io_manager: PolarsDeltaIOManager):
    df = pl.DataFrame(
        {
            "a": [1, 2, 3],
        }
    )

    @asset(io_manager_def=polars_delta_io_manager, metadata={"mode": "append"})
    def append_asset() -> pl.DataFrame:
        return df

    result = materialize(
        [append_asset],
    )

    handled_output_events = list(
        filter(lambda evt: evt.is_handled_output, result.events_for_node("append_asset"))
    )
    saved_path = handled_output_events[0].event_specific_data.metadata["path"].value  # type: ignore
    assert handled_output_events[0].event_specific_data.metadata["dagster/row_count"].value == 3  # type: ignore
    assert handled_output_events[0].event_specific_data.metadata["append_row_count"].value == 3  # type: ignore
    assert isinstance(saved_path, str)

    result = materialize(
        [append_asset],
    )
    handled_output_events = list(
        filter(lambda evt: evt.is_handled_output, result.events_for_node("append_asset"))
    )
    assert handled_output_events[0].event_specific_data.metadata["dagster/row_count"].value == 6  # type: ignore
    assert handled_output_events[0].event_specific_data.metadata["append_row_count"].value == 3  # type: ignore

    pl_testing.assert_frame_equal(pl.concat([df, df]), pl.read_delta(saved_path))


def test_polars_delta_io_manager_overwrite_schema(
    polars_delta_io_manager: PolarsDeltaIOManager, dagster_instance: DagsterInstance
):
    @asset(io_manager_def=polars_delta_io_manager)
    def overwrite_schema_asset_1() -> pl.DataFrame:
        return pl.DataFrame(
            {
                "a": [1, 2, 3],
            }
        )

    result = materialize(
        [overwrite_schema_asset_1],
    )

    saved_path = get_saved_path(result, "overwrite_schema_asset_1")

    pl_testing.assert_frame_equal(
        pl.DataFrame(
            {
                "a": [1, 2, 3],
            }
        ),
        pl.read_delta(saved_path),
    )

    @asset(
        io_manager_def=polars_delta_io_manager,
        metadata={"overwrite_schema": True, "mode": "overwrite"},
    )
    def overwrite_schema_asset_2() -> pl.DataFrame:
        return pl.DataFrame(
            {
                "b": ["1", "2", "3"],
            }
        )

    result = materialize(
        [overwrite_schema_asset_2],
    )

    saved_path = get_saved_path(result, "overwrite_schema_asset_2")

    pl_testing.assert_frame_equal(
        pl.DataFrame(
            {
                "b": ["1", "2", "3"],
            }
        ),
        pl.read_delta(saved_path),
    )

    # test IOManager configuration works too
    @asset(
        io_manager_def=PolarsDeltaIOManager(
            base_dir=dagster_instance.storage_directory(),
            mode=DeltaWriteMode.overwrite,
            overwrite_schema=True,
        )
    )
    def overwrite_schema_asset_3() -> pl.DataFrame:
        return pl.DataFrame(
            {
                "a": [1, 2, 3],
            }
        )

    result = materialize(
        [overwrite_schema_asset_3],
    )

    saved_path = get_saved_path(result, "overwrite_schema_asset_3")

    pl_testing.assert_frame_equal(
        pl.DataFrame(
            {
                "a": [1, 2, 3],
            }
        ),
        pl.read_delta(saved_path),
    )


def test_polars_delta_io_manager_overwrite_schema_lazy(
    polars_delta_io_manager: PolarsDeltaIOManager, dagster_instance: DagsterInstance
):
    @asset(io_manager_def=polars_delta_io_manager)
    def overwrite_schema_asset_1() -> pl.LazyFrame:
        return pl.LazyFrame(
            {
                "a": [1, 2, 3],
            }
        )

    result = materialize(
        [overwrite_schema_asset_1],
    )

    saved_path = get_saved_path(result, "overwrite_schema_asset_1")

    pl_testing.assert_frame_equal(
        pl.DataFrame(
            {
                "a": [1, 2, 3],
            }
        ),
        pl.read_delta(saved_path),
    )

    @asset(
        io_manager_def=polars_delta_io_manager,
        metadata={"overwrite_schema": True, "mode": "overwrite"},
    )
    def overwrite_schema_asset_2() -> pl.LazyFrame:
        return pl.LazyFrame(
            {
                "b": ["1", "2", "3"],
            }
        )

    result = materialize(
        [overwrite_schema_asset_2],
    )

    saved_path = get_saved_path(result, "overwrite_schema_asset_2")

    pl_testing.assert_frame_equal(
        pl.DataFrame(
            {
                "b": ["1", "2", "3"],
            }
        ),
        pl.read_delta(saved_path),
    )

    # test IOManager configuration works too
    @asset(
        io_manager_def=PolarsDeltaIOManager(
            base_dir=dagster_instance.storage_directory(),
            mode=DeltaWriteMode.overwrite,
            overwrite_schema=True,
        )
    )
    def overwrite_schema_asset_3() -> pl.LazyFrame:
        return pl.LazyFrame(
            {
                "a": [1, 2, 3],
            }
        )

    result = materialize(
        [overwrite_schema_asset_3],
    )

    saved_path = get_saved_path(result, "overwrite_schema_asset_3")

    pl_testing.assert_frame_equal(
        pl.DataFrame(
            {
                "a": [1, 2, 3],
            }
        ),
        pl.read_delta(saved_path),
    )


def test_polars_delta_native_partitioning(
    polars_delta_io_manager: PolarsDeltaIOManager, df_for_delta: pl.DataFrame
):
    manager = polars_delta_io_manager
    df = df_for_delta

    partitions_def = StaticPartitionsDefinition(["a", "b"])

    @asset(
        io_manager_def=manager,
        partitions_def=partitions_def,
        metadata={
            "partition_by": "partition",
            "delta_write_options": {"engine": "pyarrow"},
        },
    )
    def upstream_partitioned(context: OpExecutionContext) -> pl.DataFrame:
        return df.with_columns(pl.lit(context.partition_key).alias("partition"))

    @asset(io_manager_def=manager)
    def downstream_load_multiple_partitions_as_single_df(
        upstream_partitioned: pl.DataFrame,
    ) -> None:
        assert set(upstream_partitioned["partition"].unique()) == {"a", "b"}

    for partition_key in ["a", "b"]:
        result = materialize(
            [upstream_partitioned],
            partition_key=partition_key,
        )
        saved_path = get_saved_path(result, "upstream_partitioned")
        assert saved_path.endswith(
            "upstream_partitioned.delta"
        ), saved_path  # DeltaLake should handle partitioning!
        assert DeltaTable(saved_path).metadata().partition_columns == ["partition"]

    materialize(
        [
            upstream_partitioned.to_source_asset(),
            downstream_load_multiple_partitions_as_single_df,
        ],
    )


def test_polars_delta_native_multi_partitions(
    polars_delta_io_manager: PolarsDeltaIOManager, df_for_delta: pl.DataFrame
):
    manager = polars_delta_io_manager
    df = df_for_delta

    partitions_def = MultiPartitionsDefinition(
        {
            "time": DailyPartitionsDefinition(start_date=datetime(2024, 1, 1)),
            "category": StaticPartitionsDefinition(["a", "b"]),
        }
    )

    @asset(
        io_manager_def=manager,
        partitions_def=partitions_def,
        metadata={
            "partition_by": {"time": "date", "category": "category"},
            "delta_write_options": {"engine": "pyarrow"},
        },
    )
    def upstream_partitioned(context: OpExecutionContext) -> pl.DataFrame:
        partition_key = context.partition_key
        assert isinstance(partition_key, MultiPartitionKey)
        return df.with_columns(
            pl.lit(partition_key.keys_by_dimension["time"])
            .str.strptime(pl.Date, "%Y-%m-%d")
            .alias("date"),
            pl.lit(partition_key.keys_by_dimension["category"]).alias("category"),
        )

    @asset(io_manager_def=manager)
    def downstream_load_multiple_partitions_as_single_df(
        upstream_partitioned: pl.DataFrame,
    ) -> None:
        assert set(upstream_partitioned["category"].unique()) == {"a", "b"}
        assert set(upstream_partitioned["date"].unique()) == {
            datetime(2024, 1, 1).date(),
            datetime(2024, 1, 2).date(),
        }

    for date in ["2024-01-01", "2024-01-02"]:
        for category in ["a", "b"]:
            materialize([upstream_partitioned], partition_key=f"{category}|{date}")

    materialize(
        [
            upstream_partitioned.to_source_asset(),
            downstream_load_multiple_partitions_as_single_df,
        ],
    )


def test_polars_delta_native_partitioning_loading_single_partition(
    polars_delta_io_manager: PolarsDeltaIOManager, df_for_delta: pl.DataFrame
):
    manager = polars_delta_io_manager
    df = df_for_delta

    partitions_def = StaticPartitionsDefinition(["a", "b"])

    @asset(
        io_manager_def=manager,
        partitions_def=partitions_def,
        metadata={
            "partition_by": "partition",
            "delta_write_options": {"engine": "pyarrow"},
        },
    )
    def upstream_partitioned(context: OpExecutionContext) -> pl.DataFrame:
        return df.with_columns(pl.lit(context.partition_key).alias("partition"))

    @asset(io_manager_def=manager, partitions_def=partitions_def)
    def downstream_partitioned(
        context: AssetExecutionContext, upstream_partitioned: pl.DataFrame
    ) -> None:
        partitions = upstream_partitioned["partition"].unique().to_list()
        assert len(partitions) == 1
        assert partitions[0] == context.partition_key

    for partition_key in ["a", "b"]:
        materialize(
            [upstream_partitioned, downstream_partitioned],
            partition_key=partition_key,
        )


def test_polars_delta_time_travel(
    polars_delta_io_manager: PolarsDeltaIOManager, df_for_delta: pl.DataFrame
):
    manager = polars_delta_io_manager
    df = df_for_delta

    class UpstreamConfig(Config):
        foo: str

    @asset(io_manager_def=manager)
    def upstream(context: OpExecutionContext, config: UpstreamConfig) -> pl.DataFrame:
        return df.with_columns(pl.lit(config.foo).alias("foo"))

    for foo in ["a", "b"]:
        materialize([upstream], run_config=RunConfig(ops={"upstream": UpstreamConfig(foo=foo)}))

    # get_saved_path(result, "upstream")

    @asset(ins={"upstream": AssetIn(metadata={"version": 0})})
    def downstream_0(upstream: pl.DataFrame) -> None:
        assert upstream["foo"].head(1).item() == "a"

    materialize(
        [
            upstream.to_source_asset(),
            downstream_0,
        ]
    )

    @asset(ins={"upstream": AssetIn(metadata={"version": "1"})})
    def downstream_1(upstream: pl.DataFrame) -> None:
        assert upstream["foo"].head(1).item() == "b"

    materialize(
        [
            upstream.to_source_asset(),
            downstream_1,
        ]
    )
