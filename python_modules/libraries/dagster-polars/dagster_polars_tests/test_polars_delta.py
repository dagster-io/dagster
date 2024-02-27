import shutil
import time
from typing import Dict

import polars as pl
import polars.testing as pl_testing
import pytest
from dagster import (
    AssetExecutionContext,
    AssetIn,
    Config,
    DagsterInstance,
    OpExecutionContext,
    RunConfig,
    StaticPartitionsDefinition,
    asset,
    materialize,
)
from dagster_polars import PolarsDeltaIOManager
from dagster_polars.io_managers.delta import DeltaWriteMode
from deltalake import DeltaTable
from hypothesis import given, settings
from polars.testing.parametric import dataframes

from dagster_polars_tests.utils import get_saved_path

# TODO: remove pl.Time once it's supported
# TODO: remove pl.Duration pl.Duration once it's supported
# https://github.com/pola-rs/polars/issues/9631
# TODO: remove UInt types once they are supported
#  https://github.com/pola-rs/polars/issues/9627


@pytest.mark.flaky(reruns=5)
@given(
    df=dataframes(
        excluded_dtypes=[
            pl.Categorical,
            pl.Duration,
            pl.Time,
            pl.UInt8,
            pl.UInt16,
            pl.UInt32,
            pl.UInt64,
            pl.Datetime("ns", None),
        ],
        min_size=5,
        allow_infinities=False,
    )
)
@settings(max_examples=50, deadline=None)
def test_polars_delta_io_manager(
    session_polars_delta_io_manager: PolarsDeltaIOManager, df: pl.DataFrame
):
    time.sleep(0.2)  # too frequent writes mess up DeltaLake concurrent

    @asset(io_manager_def=session_polars_delta_io_manager, metadata={"overwrite_schema": True})
    def upstream() -> pl.DataFrame:
        return df

    @asset(io_manager_def=session_polars_delta_io_manager, metadata={"overwrite_schema": True})
    def downstream(upstream: pl.LazyFrame) -> pl.DataFrame:
        return upstream.collect(streaming=True)

    result = materialize(
        [upstream, downstream],
    )

    handled_output_events = list(
        filter(lambda evt: evt.is_handled_output, result.events_for_node("upstream"))
    )

    saved_path = handled_output_events[0].event_specific_data.metadata["path"].value  # type: ignore[index,union-attr]
    assert isinstance(saved_path, str)
    pl_testing.assert_frame_equal(df, pl.read_delta(saved_path))
    shutil.rmtree(saved_path)  # cleanup manually because of hypothesis


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
    assert handled_output_events[0].event_specific_data.metadata["row_count"].value == 3  # type: ignore
    assert handled_output_events[0].event_specific_data.metadata["append_row_count"].value == 3  # type: ignore
    assert isinstance(saved_path, str)

    result = materialize(
        [append_asset],
    )
    handled_output_events = list(
        filter(lambda evt: evt.is_handled_output, result.events_for_node("append_asset"))
    )
    assert handled_output_events[0].event_specific_data.metadata["row_count"].value == 6  # type: ignore
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
        metadata={"partition_by": "partition"},
    )
    def upstream_partitioned(context: OpExecutionContext) -> pl.DataFrame:
        return df.with_columns(pl.lit(context.partition_key).alias("partition"))

    lenghts = {}

    @asset(io_manager_def=manager)
    def downstream_load_multiple_partitions(upstream_partitioned: Dict[str, pl.LazyFrame]) -> None:
        for partition, _ldf in upstream_partitioned.items():
            assert isinstance(_ldf, pl.LazyFrame), type(_ldf)
            _df = _ldf.collect()
            assert (_df.select(pl.col("partition").eq(partition).alias("eq")))["eq"].all()
            lenghts[partition] = len(_df)

        assert set(upstream_partitioned.keys()) == {"a", "b"}, upstream_partitioned.keys()

    saved_path = None

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

    assert saved_path is not None
    written_df = pl.read_delta(saved_path)

    assert len(written_df) == len(df) * 2
    assert set(written_df["partition"].unique()) == {"a", "b"}

    materialize(
        [
            upstream_partitioned.to_source_asset(),
            downstream_load_multiple_partitions,
        ],
    )

    @asset(io_manager_def=manager)
    def downstream_load_multiple_partitions_as_single_df(
        upstream_partitioned: pl.DataFrame,
    ) -> None:
        assert set(upstream_partitioned["partition"].unique()) == {"a", "b"}

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
        metadata={"partition_by": "partition"},
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
