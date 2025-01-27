from datetime import date, datetime
from typing import Optional

import dagster._check as check
import pytest
from dagster import (
    AssetExecutionContext,
    AssetMaterialization,
    AssetOut,
    AssetsDefinition,
    AssetSpec,
    DagsterInstance,
    DagsterInvalidDefinitionError,
    DailyPartitionsDefinition,
    DynamicPartitionsDefinition,
    HourlyPartitionsDefinition,
    InputContext,
    IOManager,
    IOManagerDefinition,
    MaterializeResult,
    MultiPartitionKey,
    MultiPartitionsDefinition,
    Output,
    OutputContext,
    PartitionsDefinition,
    SourceAsset,
    StaticPartitionsDefinition,
    build_asset_context,
    daily_partitioned_config,
    define_asset_job,
    hourly_partitioned_config,
    materialize,
)
from dagster._check import CheckError
from dagster._core.definitions import asset, multi_asset
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.materialize import materialize_to_memory
from dagster._core.definitions.metadata.metadata_value import IntMetadataValue, TextMetadataValue
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.time_window_partitions import TimeWindow
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.event_api import EventRecordsFilter
from dagster._core.events import DagsterEventType
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)
from dagster._core.test_utils import (
    assert_namedtuple_lists_equal,
    freeze_time,
    ignore_warning,
    raise_exception_on_warnings,
)
from dagster._time import create_datetime, parse_time_string


@pytest.fixture(autouse=True)
def error_on_warning():
    raise_exception_on_warnings()


def get_upstream_partitions_for_partition_range(
    downstream_assets_def: AssetsDefinition,
    downstream_asset_key: AssetKey,
    upstream_partitions_def: PartitionsDefinition,
    upstream_asset_key: AssetKey,
    downstream_partition_key_range: Optional[PartitionKeyRange],
) -> PartitionKeyRange:
    if upstream_partitions_def is None:
        check.failed("upstream asset is not partitioned")

    downstream_partition_mapping = downstream_assets_def.infer_partition_mapping(
        downstream_asset_key, upstream_asset_key, upstream_partitions_def
    )
    downstream_partitions_def = downstream_assets_def.partitions_def
    downstream_partitions_subset = (
        downstream_partitions_def.empty_subset().with_partition_keys(
            downstream_partitions_def.get_partition_keys_in_range(downstream_partition_key_range)
        )
        if downstream_partitions_def and downstream_partition_key_range
        else None
    )
    upstream_partitions_subset = (
        downstream_partition_mapping.get_upstream_mapped_partitions_result_for_partitions(
            downstream_partitions_subset,
            downstream_partitions_def,
            upstream_partitions_def,
        ).partitions_subset
    )
    upstream_key_ranges = upstream_partitions_subset.get_partition_key_ranges(
        upstream_partitions_def
    )
    check.invariant(len(upstream_key_ranges) == 1)
    return upstream_key_ranges[0]


def get_downstream_partitions_for_partition_range(
    downstream_assets_def: AssetsDefinition,
    downstream_asset_key: AssetKey,
    upstream_assets_def: AssetsDefinition,
    upstream_asset_key: AssetKey,
    upstream_partition_key_range: PartitionKeyRange,
) -> PartitionKeyRange:
    if downstream_assets_def.partitions_def is None:
        check.failed("downstream asset is not partitioned")

    if upstream_assets_def.partitions_def is None:
        check.failed("upstream asset is not partitioned")

    downstream_partition_mapping = downstream_assets_def.infer_partition_mapping(
        downstream_asset_key, upstream_asset_key, upstream_assets_def.partitions_def
    )
    upstream_partitions_def = upstream_assets_def.partitions_def
    upstream_partitions_subset = upstream_partitions_def.empty_subset().with_partition_keys(
        upstream_partitions_def.get_partition_keys_in_range(upstream_partition_key_range)
    )
    downstream_partitions_subset = (
        downstream_partition_mapping.get_downstream_partitions_for_partitions(
            upstream_partitions_subset,
            upstream_partitions_def,
            downstream_assets_def.partitions_def,
        )
    )
    downstream_key_ranges = downstream_partitions_subset.get_partition_key_ranges(
        downstream_assets_def.partitions_def
    )
    check.invariant(len(downstream_key_ranges) == 1)
    return downstream_key_ranges[0]


def test_assets_with_same_partitioning():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])

    @asset(partitions_def=partitions_def)
    def upstream_asset():
        pass

    @asset(partitions_def=partitions_def)
    def downstream_asset(upstream_asset):
        assert upstream_asset

    assert get_upstream_partitions_for_partition_range(
        downstream_asset,
        downstream_asset.key,
        upstream_asset.partitions_def,  # pyright: ignore[reportArgumentType]
        AssetKey("upstream_asset"),
        PartitionKeyRange("a", "c"),
    ) == PartitionKeyRange("a", "c")

    assert get_downstream_partitions_for_partition_range(
        downstream_asset,
        downstream_asset.key,
        upstream_asset,
        AssetKey("upstream_asset"),
        PartitionKeyRange("a", "c"),
    ) == PartitionKeyRange("a", "c")


def test_single_partitioned_asset_job():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert context.asset_partition_key == "b"
            assert context.asset_partitions_def == partitions_def

        def load_input(self, context):
            assert False, "shouldn't get here"

    @asset(partitions_def=partitions_def)
    def my_asset(context: AssetExecutionContext):
        assert context.assets_def.partitions_def == partitions_def

    result = materialize(
        assets=[my_asset],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key="b",
    )
    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("my_asset"),
        [AssetMaterialization(asset_key=AssetKey(["my_asset"]), partition="b")],
        exclude_fields=["tags"],
    )


def test_two_partitioned_assets_job():
    @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c", "d"]))
    def upstream():
        pass

    @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c", "d"]))
    def downstream(upstream):
        assert upstream is None

    result = materialize_to_memory(assets=[upstream, downstream], partition_key="b")
    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("upstream"),
        [AssetMaterialization(AssetKey(["upstream"]), partition="b")],
        exclude_fields=["tags"],
    )
    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("downstream"),
        [AssetMaterialization(AssetKey(["downstream"]), partition="b")],
        exclude_fields=["tags"],
    )


def test_assets_job_with_different_partitions_defs():
    with pytest.raises(DagsterInvalidDefinitionError):

        @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c"]))
        def upstream():
            pass

        @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c", "d"]))
        def downstream(upstream):
            assert upstream is None

        Definitions(
            assets=[upstream, downstream],
            jobs=[define_asset_job("my_job", selection=[upstream, downstream])],
        ).get_job_def("my_job")


def test_access_partition_keys_from_context_direct_invocation():
    partitions_def = StaticPartitionsDefinition(["a"])

    @asset(partitions_def=partitions_def)
    def partitioned_asset(context: AssetExecutionContext):
        assert context.partition_key == "a"

    context = build_asset_context(partition_key="a")

    # check unbound context
    assert context.partition_key == "a"

    # check bound context
    partitioned_asset(context)

    # check failure for non-partitioned asset
    @asset
    def non_partitioned_asset(context: AssetExecutionContext):
        with pytest.raises(
            CheckError, match="Tried to access partition_key for a non-partitioned run"
        ):
            _ = context.partition_key

    context = build_asset_context()
    non_partitioned_asset(context)


def test_access_partition_keys_from_context_only_one_asset_partitioned():
    upstream_partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            if context.op_def.name == "upstream_asset":
                assert context.asset_partition_key == "b"
            elif context.op_def.name in ["downstream_asset", "double_downstream_asset"]:
                assert not context.has_asset_partitions
                with pytest.raises(Exception):  # TODO: better error message
                    assert context.asset_partition_key_range
            else:
                assert False

        def load_input(self, context):
            if context.op_def.name == "double_downstream_asset":
                assert not context.has_asset_partitions
            else:
                assert context.has_asset_partitions
                assert context.asset_partition_key_range == PartitionKeyRange("a", "c")

    @asset(partitions_def=upstream_partitions_def)
    def upstream_asset(context: AssetExecutionContext):
        assert context.partition_key == "b"

    @asset
    def downstream_asset(upstream_asset):
        assert upstream_asset is None

    @asset
    def double_downstream_asset(downstream_asset):
        assert downstream_asset is None

    result = materialize(
        assets=[upstream_asset, downstream_asset, double_downstream_asset],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key="b",
    )
    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("upstream_asset"),
        [AssetMaterialization(asset_key=AssetKey(["upstream_asset"]), partition="b")],
        exclude_fields=["tags"],
    )

    assert materialize(
        assets=[upstream_asset.to_source_assets()[0], downstream_asset, double_downstream_asset],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    ).success


def test_output_context_asset_partitions_time_window():
    class MyIOManager(IOManager):
        def handle_output(self, context, _obj):
            assert context.asset_partitions_time_window == TimeWindow(
                parse_time_string("2021-06-06"), parse_time_string("2021-06-07")
            )

        def load_input(self, context):
            raise NotImplementedError()

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2021-05-05"))
    def my_asset():
        pass

    materialize(
        assets=[my_asset],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key="2021-06-06",
    )


def test_input_context_asset_partitions_time_window():
    partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")

    class MyIOManager(IOManager):
        def handle_output(self, context, _obj):
            assert context.asset_partitions_time_window == TimeWindow(
                parse_time_string("2021-06-06"), parse_time_string("2021-06-07")
            )

        def load_input(self, context):
            assert context.asset_partitions_time_window == TimeWindow(
                parse_time_string("2021-06-06"), parse_time_string("2021-06-07")
            )

    @asset(partitions_def=partitions_def)
    def upstream_asset():
        pass

    @asset(partitions_def=partitions_def)
    def downstream_asset(context, upstream_asset):
        assert context.asset_partitions_time_window_for_input("upstream_asset") == TimeWindow(
            parse_time_string("2021-06-06"), parse_time_string("2021-06-07")
        )
        assert upstream_asset is None

    assert materialize(
        assets=[upstream_asset, downstream_asset],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key="2021-06-06",
    ).success

    assert materialize(
        assets=[upstream_asset.to_source_assets()[0], downstream_asset],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key="2021-06-06",
    ).success


def test_cross_job_different_partitions():
    @asset(partitions_def=HourlyPartitionsDefinition(start_date="2021-05-05-00:00"))
    def hourly_asset():
        pass

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2021-05-05"))
    def daily_asset(hourly_asset):
        assert hourly_asset is None

    class CustomIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            key_range = context.asset_partition_key_range
            assert key_range.start == "2021-06-06-00:00"
            assert key_range.end == "2021-06-06-23:00"

    assert materialize(
        assets=[daily_asset, hourly_asset],
        selection=[daily_asset],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(CustomIOManager())},
        partition_key="2021-06-06",
    ).success


@ignore_warning("Class `SourceAsset` is deprecated and will be removed in 2.0.0.")
def test_source_asset_partitions():
    hourly_asset = SourceAsset(
        AssetKey("hourly_asset"),
        partitions_def=HourlyPartitionsDefinition(start_date="2021-05-05-00:00"),
    )

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2021-05-05"))
    def daily_asset(hourly_asset):
        assert hourly_asset is None

    class CustomIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            key_range = context.asset_partition_key_range
            assert key_range.start == "2021-06-06-00:00"
            assert key_range.end == "2021-06-06-23:00"

    assert materialize(
        assets=[daily_asset, hourly_asset],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(CustomIOManager())},
        partition_key="2021-06-06",
    ).success


def test_multi_assets_with_same_partitioning():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])

    @multi_asset(
        outs={
            "out1": AssetOut(key=AssetKey("upstream_asset_1")),
            "out2": AssetOut(key=AssetKey("upstream_asset_2")),
        },
        partitions_def=partitions_def,
    )
    def upstream_asset():
        pass

    @asset(partitions_def=partitions_def)
    def downstream_asset_1(upstream_asset_1: int):
        del upstream_asset_1

    @asset(partitions_def=partitions_def)
    def downstream_asset_2(upstream_asset_2: int):
        del upstream_asset_2

    assert get_upstream_partitions_for_partition_range(
        downstream_asset_1,
        downstream_asset_1.key,
        upstream_asset.partitions_def,  # pyright: ignore[reportArgumentType]
        AssetKey("upstream_asset_1"),
        PartitionKeyRange("a", "c"),
    ) == PartitionKeyRange("a", "c")

    assert get_upstream_partitions_for_partition_range(
        downstream_asset_2,
        downstream_asset_2.key,
        upstream_asset.partitions_def,  # pyright: ignore[reportArgumentType]
        AssetKey("upstream_asset_2"),
        PartitionKeyRange("a", "c"),
    ) == PartitionKeyRange("a", "c")

    assert get_downstream_partitions_for_partition_range(
        downstream_asset_1,
        downstream_asset_1.key,
        upstream_asset,
        AssetKey("upstream_asset_1"),
        PartitionKeyRange("a", "c"),
    ) == PartitionKeyRange("a", "c")

    assert get_downstream_partitions_for_partition_range(
        downstream_asset_2,
        downstream_asset_2.key,
        upstream_asset,
        AssetKey("upstream_asset_2"),
        PartitionKeyRange("a", "c"),
    ) == PartitionKeyRange("a", "c")


def test_single_partitioned_multi_asset_job():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert context.asset_partition_key == "b"

        def load_input(self, context):
            assert False, "shouldn't get here"

    @multi_asset(
        outs={
            "out1": AssetOut(key=AssetKey("my_asset_1")),
            "out2": AssetOut(key=AssetKey("my_asset_2")),
        },
        partitions_def=partitions_def,
    )
    def my_asset():
        return (Output(1, output_name="out1"), Output(2, output_name="out2"))

    result = materialize(
        assets=[my_asset],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key="b",
    )

    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("my_asset"),
        [
            AssetMaterialization(asset_key=AssetKey(["my_asset_1"]), partition="b"),
            AssetMaterialization(asset_key=AssetKey(["my_asset_2"]), partition="b"),
        ],
        exclude_fields=["tags"],
    )


def test_multi_asset_with_different_partitions_defs():
    partitions_def1 = StaticPartitionsDefinition(["a", "b", "c", "d"])
    partitions_def2 = StaticPartitionsDefinition(["1", "2", "3"])

    @multi_asset(
        specs=[
            AssetSpec("my_asset_1", partitions_def=partitions_def1),
            AssetSpec("my_asset_2", partitions_def=partitions_def2),
        ],
        can_subset=True,
    )
    def my_assets(context):
        assert context.partition_key == "b"
        assert context.partition_keys == ["b"]
        for asset_key in context.selected_asset_keys:
            yield MaterializeResult(asset_key=asset_key)

    result = materialize(assets=[my_assets], partition_key="b", selection=["my_asset_1"])
    assert result.success

    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("my_assets"),
        [
            AssetMaterialization(asset_key=AssetKey(["my_asset_1"]), partition="b"),
        ],
        exclude_fields=["tags"],
    )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Selected assets must have the same partitions definitions, but the selected assets ",
    ):
        materialize(assets=[my_assets], partition_key="b")


def test_multi_asset_with_differrent_partitions_def_and_top_level_group_name():
    partitions_def1 = DailyPartitionsDefinition(start_date="2020-01-01")
    partitions_def2 = StaticPartitionsDefinition(["1", "2", "3"])

    @multi_asset(
        specs=[
            AssetSpec("my_asset_1", partitions_def=partitions_def1),
            AssetSpec("my_asset_2", partitions_def=partitions_def2),
        ],
        can_subset=True,
        group_name="my_group",
    )
    def my_assets(context): ...

    assert len(list(my_assets.specs or [])) == 2
    for spec in my_assets.specs:
        assert spec.group_name == "my_group"

    pds = {spec.partitions_def for spec in my_assets.specs}
    assert pds == {partitions_def1, partitions_def2}


def test_multi_asset_with_differrent_group_names_and_top_level_partitions_def():
    partitions_def1 = DailyPartitionsDefinition(start_date="2020-01-01")

    @multi_asset(
        specs=[
            AssetSpec("my_asset_1", group_name="group1"),
            AssetSpec("my_asset_2", group_name="group2"),
        ],
        can_subset=True,
        partitions_def=partitions_def1,
    )
    def my_assets(context): ...

    assert len(list(my_assets.specs or [])) == 2
    for spec in my_assets.specs:
        assert spec.partitions_def == partitions_def1

    group_names = {spec.group_name for spec in my_assets.specs}
    assert group_names == {"group1", "group2"}


def test_multi_asset_with_different_partitions_defs_partition_key_range():
    partitions_def1 = DailyPartitionsDefinition(start_date="2020-01-01")
    partitions_def2 = StaticPartitionsDefinition(["1", "2", "3"])

    @multi_asset(
        specs=[
            AssetSpec("my_asset_1", partitions_def=partitions_def1),
            AssetSpec("my_asset_2", partitions_def=partitions_def2),
        ],
        can_subset=True,
    )
    def my_assets(context):
        assert context.partition_keys == ["2020-01-01", "2020-01-02", "2020-01-03"]
        assert context.partition_key_range == PartitionKeyRange("2020-01-01", "2020-01-03")
        assert context.partition_time_window == TimeWindow(
            partitions_def1.time_window_for_partition_key("2020-01-01").start,
            partitions_def1.time_window_for_partition_key("2020-01-03").end,
        )
        for asset_key in context.selected_asset_keys:
            yield MaterializeResult(asset_key=asset_key)

    result = materialize(
        assets=[my_assets],
        selection=["my_asset_1"],
        tags={
            ASSET_PARTITION_RANGE_START_TAG: "2020-01-01",
            ASSET_PARTITION_RANGE_END_TAG: "2020-01-03",
        },
    )
    assert result.success

    materializations = result.asset_materializations_for_node("my_assets")
    assert len(materializations) == 3
    assert {
        (materialization.asset_key, materialization.partition)
        for materialization in materializations
    } == {
        (AssetKey(["my_asset_1"]), "2020-01-01"),
        (AssetKey(["my_asset_1"]), "2020-01-02"),
        (AssetKey(["my_asset_1"]), "2020-01-03"),
    }


def test_two_partitioned_multi_assets_job():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])

    @multi_asset(
        outs={
            "out1": AssetOut(key=AssetKey("upstream_asset_1")),
            "out2": AssetOut(key=AssetKey("upstream_asset_2")),
        },
        partitions_def=partitions_def,
    )
    def upstream_asset():
        return (Output(1, output_name="out1"), Output(2, output_name="out2"))

    @asset(partitions_def=partitions_def)
    def downstream_asset_1(upstream_asset_1: int):
        del upstream_asset_1

    @asset(partitions_def=partitions_def)
    def downstream_asset_2(upstream_asset_2: int):
        del upstream_asset_2

    result = materialize_to_memory(
        assets=[upstream_asset, downstream_asset_1, downstream_asset_2], partition_key="b"
    )

    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("upstream_asset"),
        [
            AssetMaterialization(AssetKey(["upstream_asset_1"]), partition="b"),
            AssetMaterialization(AssetKey(["upstream_asset_2"]), partition="b"),
        ],
        exclude_fields=["tags"],
    )

    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("downstream_asset_1"),
        [AssetMaterialization(AssetKey(["downstream_asset_1"]), partition="b")],
        exclude_fields=["tags"],
    )

    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("downstream_asset_2"),
        [AssetMaterialization(AssetKey(["downstream_asset_2"]), partition="b")],
        exclude_fields=["tags"],
    )


def test_job_config_with_asset_partitions():
    daily_partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")

    @asset(config_schema={"a": int}, partitions_def=daily_partitions_def)
    def asset1(context):
        assert context.op_execution_context.op_config["a"] == 5
        assert context.partition_key == "2020-01-01"

    the_job = define_asset_job("job", config={"ops": {"asset1": {"config": {"a": 5}}}}).resolve(
        asset_graph=AssetGraph.from_assets([asset1])
    )

    assert the_job.execute_in_process(partition_key="2020-01-01").success
    assert (
        the_job.get_subset(asset_selection={AssetKey("asset1")})
        .execute_in_process(partition_key="2020-01-01")
        .success
    )


def test_job_partitioned_config_with_asset_partitions():
    daily_partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")

    @asset(config_schema={"day_of_month": int}, partitions_def=daily_partitions_def)
    def asset1(context):
        assert context.op_execution_context.op_config["day_of_month"] == 1
        assert context.partition_key == "2020-01-01"

    @daily_partitioned_config(start_date="2020-01-01")
    def myconfig(start, _end):
        return {"ops": {"asset1": {"config": {"day_of_month": start.day}}}}

    the_job = define_asset_job("job", config=myconfig).resolve(
        asset_graph=AssetGraph.from_assets([asset1])
    )

    assert the_job.execute_in_process(partition_key="2020-01-01").success


def test_mismatched_job_partitioned_config_with_asset_partitions():
    daily_partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")

    @asset(config_schema={"day_of_month": int}, partitions_def=daily_partitions_def)
    def asset1(context):
        assert context.op_execution_context.op_config["day_of_month"] == 1
        assert context.partition_key == "2020-01-01"

    @hourly_partitioned_config(start_date="2020-01-01-00:00")
    def myconfig(start, _end):
        return {"ops": {"asset1": {"config": {"day_of_month": start.day}}}}

    with pytest.raises(
        CheckError,
        match=(
            "Can't supply a PartitionedConfig for 'config' with a different PartitionsDefinition"
            " than supplied for 'partitions_def'."
        ),
    ):
        define_asset_job("job", config=myconfig).resolve(
            asset_graph=AssetGraph.from_assets([asset1])
        )


def test_partition_range_single_run() -> None:
    partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")

    @asset(partitions_def=partitions_def)
    def upstream_asset(context: AssetExecutionContext) -> None:
        key_range = PartitionKeyRange(start="2020-01-01", end="2020-01-03")
        assert context.has_partition_key_range
        assert context.partition_key_range == key_range
        assert context.partition_time_window == TimeWindow(
            partitions_def.time_window_for_partition_key(key_range.start).start,
            partitions_def.time_window_for_partition_key(key_range.end).end,
        )
        assert context.partition_keys == partitions_def.get_partition_keys_in_range(key_range)
        context.add_asset_metadata(metadata={"asset_unpartitioned": "yay"})
        context.add_output_metadata(metadata={"output_unpartitioned": "yay"})
        for i, key in enumerate(context.partition_keys):
            context.add_asset_metadata(partition_key=key, metadata={"index": i})

    @asset(partitions_def=partitions_def, deps=["upstream_asset"])
    def downstream_asset(context: AssetExecutionContext) -> None:
        assert context.asset_partition_key_range_for_input("upstream_asset") == PartitionKeyRange(
            start="2020-01-01", end="2020-01-03"
        )
        assert context.partition_key_range == PartitionKeyRange(
            start="2020-01-01", end="2020-01-03"
        )
        context.add_output_metadata(metadata={"unscoped": "yay"})

    the_job = define_asset_job("job").resolve(
        asset_graph=AssetGraph.from_assets([upstream_asset, downstream_asset])
    )

    result = the_job.execute_in_process(
        tags={
            ASSET_PARTITION_RANGE_START_TAG: "2020-01-01",
            ASSET_PARTITION_RANGE_END_TAG: "2020-01-03",
        }
    )

    upstream_assets = result.asset_materializations_for_node("upstream_asset")
    downstream_assets = result.asset_materializations_for_node("downstream_asset")
    assert {materialization.partition for materialization in upstream_assets} == {
        "2020-01-01",
        "2020-01-02",
        "2020-01-03",
    }
    assert {materialization.partition for materialization in downstream_assets} == {
        "2020-01-01",
        "2020-01-02",
        "2020-01-03",
    }

    for i, mat in enumerate(upstream_assets):
        assert mat.metadata == {
            "asset_unpartitioned": TextMetadataValue("yay"),
            "output_unpartitioned": TextMetadataValue("yay"),
            "index": IntMetadataValue(i),
        }
    for mat in downstream_assets:
        assert mat.metadata == {"unscoped": TextMetadataValue("yay")}


def test_multipartition_range_single_run():
    partitions_def = MultiPartitionsDefinition(
        {
            "date": DailyPartitionsDefinition(start_date="2020-01-01"),
            "abc": StaticPartitionsDefinition(["a", "b", "c"]),
        }
    )

    @asset(partitions_def=partitions_def)
    def multipartitioned_asset(context: AssetExecutionContext) -> None:
        key_range = context.partition_key_range

        assert isinstance(key_range.start, MultiPartitionKey)
        assert isinstance(key_range.end, MultiPartitionKey)
        assert key_range.start == MultiPartitionKey({"date": "2020-01-01", "abc": "a"})
        assert key_range.end == MultiPartitionKey({"date": "2020-01-03", "abc": "a"})

        assert all(isinstance(key, MultiPartitionKey) for key in context.partition_keys)

    the_job = define_asset_job("job").resolve(
        asset_graph=AssetGraph.from_assets([multipartitioned_asset])
    )

    result = the_job.execute_in_process(
        tags={
            ASSET_PARTITION_RANGE_START_TAG: "a|2020-01-01",
            ASSET_PARTITION_RANGE_END_TAG: "a|2020-01-03",
        }
    )
    assert result.success
    assert {
        materialization.partition
        for materialization in result.asset_materializations_for_node("multipartitioned_asset")
    } == {
        MultiPartitionKey({"date": "2020-01-01", "abc": "a"}),
        MultiPartitionKey({"date": "2020-01-02", "abc": "a"}),
        MultiPartitionKey({"date": "2020-01-03", "abc": "a"}),
    }


def test_multipartitioned_asset_partitions_time_window():
    partitions_def = MultiPartitionsDefinition(
        {
            "date": DailyPartitionsDefinition(start_date="2023-01-01"),
            "abc": StaticPartitionsDefinition(["a", "b", "c"]),
        }
    )

    @asset(partitions_def=partitions_def)
    def multipartitioned_asset(context) -> None:
        pass

    class CustomIOManager(IOManager):
        def handle_output(self, context: OutputContext, obj):
            assert context.asset_partitions_time_window == TimeWindow(
                parse_time_string("2023-01-01"), parse_time_string("2023-01-02")
            )

        def load_input(self, context: InputContext):
            assert context.asset_partitions_time_window == TimeWindow(
                parse_time_string("2023-01-01"), parse_time_string("2023-01-02")
            )

    assert materialize(
        assets=[multipartitioned_asset],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(CustomIOManager())},
        partition_key="a|2023-01-01",
    ).success


def test_dynamic_partition_range_single_run():
    partitions_def = DynamicPartitionsDefinition(name="yolo")

    @asset(partitions_def=partitions_def)
    def dynamicpartitioned_asset(context: AssetExecutionContext) -> None:
        key_range = context.partition_key_range

        assert key_range.start == "a"
        assert key_range.end == "c"

        assert len(context.partition_keys) == 3

    the_job = define_asset_job("job").resolve(
        asset_graph=AssetGraph.from_assets([dynamicpartitioned_asset])
    )

    instance = DagsterInstance.ephemeral()
    instance.add_dynamic_partitions("yolo", ["a", "b", "c"])

    result = the_job.execute_in_process(
        tags={
            ASSET_PARTITION_RANGE_START_TAG: "a",
            ASSET_PARTITION_RANGE_END_TAG: "c",
        },
        instance=instance,
    )
    assert result.success
    assert {
        materialization.partition
        for materialization in result.asset_materializations_for_node("dynamicpartitioned_asset")
    } == {"a", "b", "c"}


def test_error_on_nonexistent_upstream_partition():
    @asset(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"))
    def upstream_asset(context):
        return 1

    @asset(partitions_def=HourlyPartitionsDefinition(start_date="2020-01-01-00:00"))
    def downstream_asset(context, upstream_asset):
        return upstream_asset + 1

    with freeze_time(create_datetime(2020, 1, 2, 10, 0)):
        with pytest.raises(
            DagsterInvariantViolationError,
            match="depends on invalid partitions",
        ):
            materialize(
                [downstream_asset, upstream_asset.to_source_asset()],
                partition_key="2020-01-02-05:00",
            )


def test_asset_spec_partitions_def():
    partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")

    @multi_asset(
        specs=[AssetSpec("asset1", partitions_def=partitions_def)], partitions_def=partitions_def
    )
    def assets1(): ...

    assert assets1.partitions_def == partitions_def
    assert next(iter(assets1.specs)).partitions_def == partitions_def

    @multi_asset(specs=[AssetSpec("asset1", partitions_def=partitions_def)])
    def assets2(): ...

    assert assets2.partitions_def == partitions_def
    assert next(iter(assets2.specs)).partitions_def == partitions_def

    with pytest.raises(
        CheckError,
        match="which is different than the partitions_def provided to AssetsDefinition",
    ):

        @multi_asset(
            specs=[AssetSpec("asset1", partitions_def=StaticPartitionsDefinition(["a", "b"]))],
            partitions_def=partitions_def,
        )
        def assets3(): ...

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="If different AssetSpecs have different partitions_defs, can_subset must be True",
    ):

        @multi_asset(
            specs=[
                AssetSpec("asset1", partitions_def=partitions_def),
                AssetSpec("asset2", partitions_def=StaticPartitionsDefinition(["a", "b"])),
            ],
        )
        def assets4(): ...

    with pytest.raises(
        CheckError,
        match="If partitions_def is provided, then either all specs must have that PartitionsDefinition or none",
    ):

        @multi_asset(
            specs=[
                AssetSpec("asset1", partitions_def=partitions_def),
                AssetSpec("asset2"),
            ],
            partitions_def=partitions_def,
        )
        def assets5(): ...


def test_partitioned_asset_metadata():
    @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c"]))
    def partitioned_asset(context: AssetExecutionContext) -> None:
        context.add_asset_metadata(metadata={"asset_unpartitioned": "yay"})
        context.add_output_metadata(metadata={"output_unpartitioned": "yay"})

        context.add_asset_metadata(
            asset_key="partitioned_asset", metadata={"asset_key_specified": "yay"}
        )
        context.add_output_metadata(
            output_name=context.assets_def.get_output_name_for_asset_key(context.assets_def.key),
            metadata={"output_name_specified": "yay"},
        )

        for key in context.partition_keys:
            context.add_asset_metadata(partition_key=key, metadata={f"partition_key_{key}": "yay"})

        with pytest.raises(DagsterInvariantViolationError):
            context.add_asset_metadata(metadata={"wont_work": "yay"}, partition_key="nonce")

        with pytest.raises(DagsterInvariantViolationError):
            context.add_asset_metadata(metadata={"wont_work": "yay"}, asset_key="nonce")

        with pytest.raises(DagsterInvariantViolationError):
            context.add_output_metadata(metadata={"wont_work": "yay"}, output_name="nonce")

        # partition key is valid but not currently being targeted.
        with pytest.raises(DagsterInvariantViolationError):
            context.add_asset_metadata(
                metadata={"wont_work": "yay"}, asset_key="partitioned_asset", partition_key="c"
            )

    with instance_for_test() as instance:
        result = materialize(
            assets=[partitioned_asset],
            instance=instance,
            tags={ASSET_PARTITION_RANGE_START_TAG: "a", ASSET_PARTITION_RANGE_END_TAG: "b"},
        )
        assert result.success

        asset_materializations = result.asset_materializations_for_node("partitioned_asset")
        assert len(asset_materializations) == 2
        a_mat = next(mat for mat in asset_materializations if mat.partition == "a")
        b_mat = next(mat for mat in asset_materializations if mat.partition == "b")
        assert a_mat.metadata == {
            "asset_unpartitioned": TextMetadataValue("yay"),
            "output_unpartitioned": TextMetadataValue("yay"),
            "asset_key_specified": TextMetadataValue("yay"),
            "output_name_specified": TextMetadataValue("yay"),
            "partition_key_a": TextMetadataValue("yay"),
        }
        assert b_mat.metadata == {
            "asset_unpartitioned": TextMetadataValue("yay"),
            "output_unpartitioned": TextMetadataValue("yay"),
            "asset_key_specified": TextMetadataValue("yay"),
            "output_name_specified": TextMetadataValue("yay"),
            "partition_key_b": TextMetadataValue("yay"),
        }

        output_log = instance.event_log_storage.get_event_records(
            event_records_filter=EventRecordsFilter(event_type=DagsterEventType.STEP_OUTPUT)
        )[0]
        assert check.not_none(
            output_log.event_log_entry.dagster_event
        ).step_output_data.metadata == {
            "output_unpartitioned": TextMetadataValue("yay"),
            "output_name_specified": TextMetadataValue("yay"),
        }


def test_time_partitioned_asset_get_partition_key():
    hourly_partition_definition = HourlyPartitionsDefinition(start_date="2021-05-05-00:00")

    @asset(partitions_def=hourly_partition_definition)
    def hourly_asset():
        pass

    daily_partition_definition = DailyPartitionsDefinition(start_date="2021-05-05")

    @asset(partitions_def=daily_partition_definition)
    def daily_asset():
        pass

    class CustomIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            pass

    # Assert get_partition_key works with regular strings
    assert materialize(
        assets=[daily_asset],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(CustomIOManager())},
        partition_key=daily_partition_definition.get_partition_key("2022-01-01"),
    ).success
    assert materialize(
        assets=[hourly_asset],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(CustomIOManager())},
        partition_key=hourly_partition_definition.get_partition_key("2022-01-01-01:01"),
    ).success

    # Assert get_partition_key works with (valid) date
    assert materialize(
        assets=[daily_asset],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(CustomIOManager())},
        partition_key=daily_partition_definition.get_partition_key(date(2022, 1, 1)),
    ).success
    assert materialize(
        assets=[hourly_asset],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(CustomIOManager())},
        partition_key=hourly_partition_definition.get_partition_key(date(2022, 1, 1)),
    ).success

    # Assert get_partition_key works with (valid) datetime
    assert materialize(
        assets=[daily_asset],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(CustomIOManager())},
        partition_key=daily_partition_definition.get_partition_key(datetime(2022, 1, 1, 23, 1, 1)),
    ).success
    assert materialize(
        assets=[hourly_asset],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(CustomIOManager())},
        partition_key=hourly_partition_definition.get_partition_key(datetime(2022, 1, 1, 21, 1, 1)),
    ).success

    # If we pass a date outside the defined start/end range of the asset, expect ValueError
    with pytest.raises(
        ValueError,
    ):
        materialize(
            assets=[daily_asset],
            resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(CustomIOManager())},
            partition_key=daily_partition_definition.get_partition_key(date(1970, 1, 1)),
        )
    with pytest.raises(
        ValueError,
    ):
        materialize(
            assets=[hourly_asset],
            resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(CustomIOManager())},
            partition_key=hourly_partition_definition.get_partition_key(datetime(1970, 1, 1)),
        )

    # We should also expect ValueError if we pass in an invalid value like None
    with pytest.raises(
        check.ParameterCheckError,
    ):
        materialize(
            assets=[daily_asset],
            resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(CustomIOManager())},
            partition_key=daily_partition_definition.get_partition_key(None),  # pyright: ignore[reportArgumentType]
        )
