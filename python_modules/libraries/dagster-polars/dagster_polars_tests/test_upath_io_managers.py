from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import polars as pl
import polars.testing as pl_testing
import pytest
from dagster import (
    AssetExecutionContext,
    AssetIn,
    DailyPartitionsDefinition,
    DimensionPartitionMapping,
    IdentityPartitionMapping,
    MultiPartitionKey,
    MultiPartitionMapping,
    MultiPartitionsDefinition,
    OpExecutionContext,
    StaticPartitionsDefinition,
    TimeWindowPartitionMapping,
    asset,
    materialize,
)
from dagster_polars import (
    BasePolarsUPathIOManager,
    DataFramePartitions,
    LazyFramePartitions,
    PolarsDeltaIOManager,
    PolarsParquetIOManager,
    StorageMetadata,
)
from deepdiff import DeepDiff
from packaging.version import Version

from dagster_polars_tests.utils import get_saved_path


def test_polars_upath_io_manager_stats_metadata(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, _ = io_manager_and_df

    df = pl.DataFrame({"a": [0, 1, None], "b": ["a", "b", "c"]})

    @asset(io_manager_def=manager)
    def upstream() -> pl.DataFrame:
        return df

    result = materialize(
        [upstream],
    )

    handled_output_events = list(
        filter(lambda evt: evt.is_handled_output, result.events_for_node("upstream"))
    )

    stats = handled_output_events[0].event_specific_data.metadata["stats"].value  # type: ignore

    expected_stats = {
        "a": {
            # count started ignoring null values in polars 0.20.0
            "count": 3.0 if Version(pl.__version__) < Version("0.20.0") else 2.0,
            "null_count": 1.0,
            "mean": 0.5,
            "std": 0.7071067811865476,
            "min": 0.0,
            "max": 1.0,
            "median": 0.5,
            "25%": 0.0,
            "75%": 1.0,
        },
        "b": {
            "count": "3",
            "null_count": "0",
            "mean": "null",
            "std": "null",
            "min": "a",
            "max": "c",
            "median": "null",
            "25%": "null",
            "75%": "null",
        },
    }

    # "50%" and "median" are problematic to test because they were changed in polars 0.18.0
    # so we remove them from the test
    for col in ("50%", "median"):
        for s in (stats, expected_stats):
            if col in s["a"]:  # type: ignore
                s["a"].pop(col)  # type: ignore
            if col in s["b"]:  # type: ignore
                s["b"].pop(col)  # type: ignore

    assert DeepDiff(stats, expected_stats) == {}


def test_polars_upath_io_manager_type_annotations(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, df = io_manager_and_df

    @asset(io_manager_def=manager)
    def upstream() -> pl.DataFrame:
        return df

    @asset(io_manager_def=manager)
    def downstream_default_eager(upstream) -> None:
        assert isinstance(upstream, pl.DataFrame), type(upstream)

    @asset(io_manager_def=manager)
    def downstream_eager(upstream: pl.DataFrame) -> None:
        assert isinstance(upstream, pl.DataFrame), type(upstream)

    @asset(io_manager_def=manager)
    def downstream_lazy(upstream: pl.LazyFrame) -> None:
        assert isinstance(upstream, pl.LazyFrame), type(upstream)

    partitions_def = StaticPartitionsDefinition(["a", "b"])

    @asset(io_manager_def=manager, partitions_def=partitions_def)
    def upstream_partitioned(context: OpExecutionContext) -> pl.DataFrame:
        return df.with_columns(pl.lit(context.partition_key).alias("partition"))

    @asset(io_manager_def=manager)
    def downstream_multi_partitioned_eager(upstream_partitioned: Dict[str, pl.DataFrame]) -> None:
        for _df in upstream_partitioned.values():
            assert isinstance(_df, pl.DataFrame), type(_df)
        assert set(upstream_partitioned.keys()) == {"a", "b"}, upstream_partitioned.keys()

    @asset(io_manager_def=manager)
    def downstream_multi_partitioned_lazy(upstream_partitioned: Dict[str, pl.LazyFrame]) -> None:
        for _df in upstream_partitioned.values():
            assert isinstance(_df, pl.LazyFrame), type(_df)
        assert set(upstream_partitioned.keys()) == {"a", "b"}, upstream_partitioned.keys()

    for partition_key in ["a", "b"]:
        materialize(
            [upstream_partitioned],
            partition_key=partition_key,
        )

    materialize(
        [
            upstream_partitioned.to_source_asset(),
            upstream,
            downstream_default_eager,
            downstream_eager,
            downstream_lazy,
            downstream_multi_partitioned_eager,
            downstream_multi_partitioned_lazy,
        ],
    )


def test_polars_upath_io_manager_nested_dtypes(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, df = io_manager_and_df

    @asset(io_manager_def=manager)
    def upstream() -> pl.DataFrame:
        return df

    @asset(io_manager_def=manager)
    def downstream(upstream: pl.LazyFrame) -> pl.DataFrame:
        return upstream.collect(streaming=True)

    result = materialize(
        [upstream, downstream],
    )

    saved_path = get_saved_path(result, "upstream")

    if isinstance(manager, PolarsParquetIOManager):
        pl_testing.assert_frame_equal(df, pl.read_parquet(saved_path))
    elif isinstance(manager, PolarsDeltaIOManager):
        pl_testing.assert_frame_equal(df, pl.read_delta(saved_path))
    else:
        raise ValueError(f"Test not implemented for {type(manager)}")


def test_polars_upath_io_manager_input_optional_eager(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, df = io_manager_and_df

    @asset(io_manager_def=manager)
    def upstream() -> pl.DataFrame:
        return df

    @asset(io_manager_def=manager)
    def downstream(upstream: Optional[pl.DataFrame]) -> pl.DataFrame:
        assert upstream is not None
        return upstream

    materialize(
        [upstream, downstream],
    )


def test_polars_upath_io_manager_input_optional_lazy(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, df = io_manager_and_df

    @asset(io_manager_def=manager)
    def upstream() -> pl.DataFrame:
        return df

    @asset(io_manager_def=manager)
    def downstream(upstream: Optional[pl.LazyFrame]) -> pl.DataFrame:
        assert upstream is not None
        return upstream.collect()

    materialize(
        [upstream, downstream],
    )


def test_polars_upath_io_manager_input_dict_eager(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, df = io_manager_and_df

    @asset(io_manager_def=manager, partitions_def=StaticPartitionsDefinition(["a", "b"]))
    def upstream(context: AssetExecutionContext) -> pl.DataFrame:
        return df.with_columns(pl.lit(context.partition_key).alias("partition"))

    @asset(io_manager_def=manager)
    def downstream(upstream: Dict[str, pl.DataFrame]) -> pl.DataFrame:
        dfs = []
        for df in upstream.values():
            assert isinstance(df, pl.DataFrame)
            dfs.append(df)
        return pl.concat(dfs)

    for partition_key in ["a", "b"]:
        materialize(
            [upstream],
            partition_key=partition_key,
        )

    materialize(
        [upstream.to_source_asset(), downstream],
    )


def test_polars_upath_io_manager_input_dict_lazy(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, df = io_manager_and_df

    @asset(io_manager_def=manager, partitions_def=StaticPartitionsDefinition(["a", "b"]))
    def upstream(context: AssetExecutionContext) -> pl.DataFrame:
        return df.with_columns(pl.lit(context.partition_key).alias("partition"))

    @asset(io_manager_def=manager)
    def downstream(upstream: Dict[str, pl.LazyFrame]) -> pl.DataFrame:
        dfs = []
        for df in upstream.values():
            assert isinstance(df, pl.LazyFrame)
            dfs.append(df)
        return pl.concat(dfs).collect()

    for partition_key in ["a", "b"]:
        materialize(
            [upstream],
            partition_key=partition_key,
        )

    materialize(
        [upstream.to_source_asset(), downstream],
    )


def test_polars_upath_io_manager_input_data_frame_partitions(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, df = io_manager_and_df

    @asset(io_manager_def=manager, partitions_def=StaticPartitionsDefinition(["a", "b"]))
    def upstream(context: AssetExecutionContext) -> pl.DataFrame:
        return df.with_columns(pl.lit(context.partition_key).alias("partition"))

    @asset(io_manager_def=manager)
    def downstream(upstream: DataFramePartitions) -> pl.DataFrame:
        dfs = []
        for df in upstream.values():
            assert isinstance(df, pl.DataFrame)
            dfs.append(df)
        return pl.concat(dfs)

    for partition_key in ["a", "b"]:
        materialize(
            [upstream],
            partition_key=partition_key,
        )

    materialize(
        [upstream.to_source_asset(), downstream],
    )


def test_polars_upath_io_manager_input_lazy_frame_partitions_lazy(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, df = io_manager_and_df

    @asset(io_manager_def=manager, partitions_def=StaticPartitionsDefinition(["a", "b"]))
    def upstream(context: AssetExecutionContext) -> pl.DataFrame:
        return df.with_columns(pl.lit(context.partition_key).alias("partition"))

    @asset(io_manager_def=manager)
    def downstream(upstream: LazyFramePartitions) -> pl.DataFrame:
        dfs = []
        for df in upstream.values():
            assert isinstance(df, pl.LazyFrame)
            dfs.append(df)
        return pl.concat(dfs).collect()

    for partition_key in ["a", "b"]:
        materialize(
            [upstream],
            partition_key=partition_key,
        )

    materialize(
        [upstream.to_source_asset(), downstream],
    )


def test_polars_upath_io_manager_input_optional_eager_return_none(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, df = io_manager_and_df

    @asset(io_manager_def=manager)
    def upstream() -> pl.DataFrame:
        return df

    @asset
    def downstream(upstream: Optional[pl.DataFrame]):
        assert upstream is None

    materialize(
        [upstream.to_source_asset(), downstream],
    )


def test_polars_upath_io_manager_output_optional_eager(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, df = io_manager_and_df

    @asset(io_manager_def=manager)
    def upstream() -> Optional[pl.DataFrame]:
        return None

    @asset(io_manager_def=manager)
    def downstream(upstream: Optional[pl.DataFrame]) -> Optional[pl.DataFrame]:
        assert upstream is None
        return upstream

    materialize(
        [upstream, downstream],
    )


def test_polars_upath_io_manager_output_optional_lazy(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, df = io_manager_and_df

    @asset(io_manager_def=manager)
    def upstream() -> Optional[pl.DataFrame]:
        return None

    @asset(io_manager_def=manager)
    def downstream(upstream: Optional[pl.LazyFrame]) -> Optional[pl.DataFrame]:
        assert upstream is None
        return upstream

    materialize(
        [upstream, downstream],
    )


IO_MANAGERS_SUPPORTING_STORAGE_METADATA = (
    PolarsParquetIOManager,
    PolarsDeltaIOManager,
)


def check_skip_storage_metadata_test(io_manager_def: BasePolarsUPathIOManager):
    if not isinstance(io_manager_def, IO_MANAGERS_SUPPORTING_STORAGE_METADATA):
        pytest.skip(f"Only {IO_MANAGERS_SUPPORTING_STORAGE_METADATA} support storage metadata")


@pytest.fixture
def metadata() -> StorageMetadata:
    return {"a": 1, "b": "2", "c": [1, 2, 3], "d": {"e": 1}, "f": [1, 2, 3, {"g": 1}]}


def test_upath_io_manager_storage_metadata_eager(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame], metadata: StorageMetadata
):
    io_manager_def, df = io_manager_and_df
    check_skip_storage_metadata_test(io_manager_def)

    @asset(io_manager_def=io_manager_def)
    def upstream() -> Tuple[pl.DataFrame, StorageMetadata]:
        return df, metadata

    @asset(io_manager_def=io_manager_def)
    def downstream(upstream: Tuple[pl.DataFrame, StorageMetadata]) -> None:
        loaded_df, upstream_metadata = upstream
        assert upstream_metadata == metadata
        pl_testing.assert_frame_equal(loaded_df, df)

    materialize(
        [upstream, downstream],
    )


def test_upath_io_manager_storage_metadata_lazy(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame], metadata: StorageMetadata
):
    io_manager_def, df = io_manager_and_df
    check_skip_storage_metadata_test(io_manager_def)

    @asset(io_manager_def=io_manager_def)
    def upstream() -> Tuple[pl.DataFrame, StorageMetadata]:
        return df, metadata

    @asset(io_manager_def=io_manager_def)
    def downstream(upstream: Tuple[pl.LazyFrame, StorageMetadata]) -> None:
        df, upstream_metadata = upstream
        assert isinstance(df, pl.LazyFrame)
        assert upstream_metadata == metadata

    materialize(
        [upstream, downstream],
    )


def test_upath_io_manager_storage_metadata_optional_eager_exists(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame], metadata: StorageMetadata
):
    io_manager_def, df = io_manager_and_df
    check_skip_storage_metadata_test(io_manager_def)

    @asset(io_manager_def=io_manager_def)
    def upstream() -> Optional[Tuple[pl.DataFrame, StorageMetadata]]:
        return df, metadata

    @asset(io_manager_def=io_manager_def)
    def downstream(upstream: Optional[Tuple[pl.DataFrame, StorageMetadata]]) -> None:
        assert upstream is not None
        df, upstream_metadata = upstream
        assert upstream_metadata == metadata

    materialize(
        [upstream, downstream],
    )


def test_upath_io_manager_storage_metadata_optional_eager_missing(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame], metadata: StorageMetadata
):
    io_manager_def, df = io_manager_and_df
    check_skip_storage_metadata_test(io_manager_def)

    @asset(io_manager_def=io_manager_def)
    def upstream() -> Optional[Tuple[pl.DataFrame, StorageMetadata]]:
        return None

    @asset(io_manager_def=io_manager_def)
    def downstream(upstream: Optional[Tuple[pl.DataFrame, StorageMetadata]]) -> None:
        assert upstream is None

    materialize(
        [upstream, downstream],
    )


def test_upath_io_manager_storage_metadata_optional_lazy_exists(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame], metadata: StorageMetadata
):
    io_manager_def, df = io_manager_and_df
    check_skip_storage_metadata_test(io_manager_def)

    @asset(io_manager_def=io_manager_def)
    def upstream() -> Optional[Tuple[pl.DataFrame, StorageMetadata]]:
        return df, metadata

    @asset(io_manager_def=io_manager_def)
    def downstream(upstream: Optional[Tuple[pl.LazyFrame, StorageMetadata]]) -> None:
        assert upstream is not None
        df, upstream_metadata = upstream
        assert isinstance(df, pl.LazyFrame)
        assert upstream_metadata == metadata

    materialize(
        [upstream, downstream],
    )


def test_upath_io_manager_storage_metadata_optional_lazy_missing(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame], metadata: StorageMetadata
):
    io_manager_def, df = io_manager_and_df
    check_skip_storage_metadata_test(io_manager_def)

    @asset(io_manager_def=io_manager_def)
    def upstream() -> Optional[Tuple[pl.DataFrame, StorageMetadata]]:
        return None

    @asset(io_manager_def=io_manager_def)
    def downstream(upstream: Optional[Tuple[pl.LazyFrame, StorageMetadata]]) -> None:
        assert upstream is None

    materialize(
        [upstream, downstream],
    )


def test_upath_io_manager_multi_partitions_definition_load_multiple_partitions(
    io_manager_and_df: Tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    io_manager_def, df = io_manager_and_df

    today = datetime.now().date()

    partitions_def = MultiPartitionsDefinition(
        {
            "time": DailyPartitionsDefinition(start_date=str(today - timedelta(days=3))),
            "static": StaticPartitionsDefinition(["a"]),
        }
    )

    @asset(partitions_def=partitions_def, io_manager_def=io_manager_def)
    def upstream(context: AssetExecutionContext) -> pl.DataFrame:
        return pl.DataFrame({"partition": [str(context.partition_key)]})

    # this asset will request 2 upstream partitions
    @asset(
        io_manager_def=io_manager_def,
        partitions_def=partitions_def,
        ins={
            "upstream": AssetIn(
                partition_mapping=MultiPartitionMapping(
                    {
                        "time": DimensionPartitionMapping(
                            "time", TimeWindowPartitionMapping(start_offset=-1)
                        ),
                        "static": DimensionPartitionMapping("static", IdentityPartitionMapping()),
                    }
                )
            )
        },
    )
    def downstream(context: AssetExecutionContext, upstream: DataFramePartitions) -> None:
        assert len(upstream.values()) == 2

    materialize(
        [upstream],
        partition_key=MultiPartitionKey({"time": str(today - timedelta(days=3)), "static": "a"}),
    )
    materialize(
        [upstream],
        partition_key=MultiPartitionKey({"time": str(today - timedelta(days=2)), "static": "a"}),
    )
    # materialize([upstream], partition_key=MultiPartitionKey({"time": str(today - timedelta(days=1)), "static": "a"}))

    materialize(
        [upstream.to_source_asset(), downstream],
        partition_key=MultiPartitionKey({"time": str(today - timedelta(days=2)), "static": "a"}),
    )
