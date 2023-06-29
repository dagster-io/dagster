import warnings
from typing import Optional

import dagster._check as check
import pendulum
import pytest
from dagster import (
    AssetMaterialization,
    AssetOut,
    AssetsDefinition,
    DagsterInvalidDefinitionError,
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    IOManager,
    IOManagerDefinition,
    MultiPartitionKey,
    MultiPartitionsDefinition,
    Output,
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
from dagster._core.definitions import asset, build_assets_job, multi_asset
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.time_window_partitions import TimeWindow
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)
from dagster._core.test_utils import assert_namedtuple_lists_equal
from dagster._seven.compat.pendulum import create_pendulum_time


@pytest.fixture(autouse=True)
def error_on_warning():
    # turn off any outer warnings filters, e.g. ignores that are set in pyproject.toml
    warnings.resetwarnings()

    warnings.filterwarnings("error")


def get_upstream_partitions_for_partition_range(
    downstream_assets_def: AssetsDefinition,
    upstream_partitions_def: PartitionsDefinition,
    upstream_asset_key: AssetKey,
    downstream_partition_key_range: Optional[PartitionKeyRange],
) -> PartitionKeyRange:
    if upstream_partitions_def is None:
        check.failed("upstream asset is not partitioned")

    downstream_partition_mapping = downstream_assets_def.infer_partition_mapping(
        upstream_asset_key, upstream_partitions_def
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
            upstream_partitions_def,
        ).partitions_subset
    )
    upstream_key_ranges = upstream_partitions_subset.get_partition_key_ranges()
    check.invariant(len(upstream_key_ranges) == 1)
    return upstream_key_ranges[0]


def get_downstream_partitions_for_partition_range(
    downstream_assets_def: AssetsDefinition,
    upstream_assets_def: AssetsDefinition,
    upstream_asset_key: AssetKey,
    upstream_partition_key_range: PartitionKeyRange,
) -> PartitionKeyRange:
    if downstream_assets_def.partitions_def is None:
        check.failed("downstream asset is not partitioned")

    if upstream_assets_def.partitions_def is None:
        check.failed("upstream asset is not partitioned")

    downstream_partition_mapping = downstream_assets_def.infer_partition_mapping(
        upstream_asset_key, upstream_assets_def.partitions_def
    )
    upstream_partitions_def = upstream_assets_def.partitions_def
    upstream_partitions_subset = upstream_partitions_def.empty_subset().with_partition_keys(
        upstream_partitions_def.get_partition_keys_in_range(upstream_partition_key_range)
    )
    downstream_partitions_subset = (
        downstream_partition_mapping.get_downstream_partitions_for_partitions(
            upstream_partitions_subset,
            downstream_assets_def.partitions_def,
        )
    )
    downstream_key_ranges = downstream_partitions_subset.get_partition_key_ranges()
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
        upstream_asset.partitions_def,
        AssetKey("upstream_asset"),
        PartitionKeyRange("a", "c"),
    ) == PartitionKeyRange("a", "c")

    assert get_downstream_partitions_for_partition_range(
        downstream_asset,
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
    def my_asset(context):
        assert context.asset_partitions_def_for_output() == partitions_def

    my_job = build_assets_job(
        "my_job",
        assets=[my_asset],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )
    result = my_job.execute_in_process(partition_key="b")
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

    my_job = build_assets_job("my_job", assets=[upstream, downstream])
    result = my_job.execute_in_process(partition_key="b")
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

        build_assets_job("my_job", assets=[upstream, downstream])


def test_access_partition_keys_from_context_direct_invocation():
    partitions_def = StaticPartitionsDefinition(["a"])

    @asset(partitions_def=partitions_def)
    def partitioned_asset(context):
        assert context.asset_partition_key_for_output() == "a"

    context = build_asset_context(partition_key="a")

    # check unbound context
    assert context.asset_partition_key_for_output() == "a"

    # check bound context
    partitioned_asset(context)

    # check failure for non-partitioned asset
    @asset
    def non_partitioned_asset(context):
        with pytest.raises(
            CheckError, match="Tried to access partition_key for a non-partitioned asset"
        ):
            context.asset_partition_key_for_output()

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
    def upstream_asset(context):
        assert context.asset_partition_key_for_output() == "b"

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
                pendulum.parse("2021-06-06"), pendulum.parse("2021-06-07")
            )

        def load_input(self, context):
            raise NotImplementedError()

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2021-05-05"))
    def my_asset():
        pass

    my_job = build_assets_job(
        "my_job",
        assets=[my_asset],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )
    my_job.execute_in_process(partition_key="2021-06-06")


def test_input_context_asset_partitions_time_window():
    partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")

    class MyIOManager(IOManager):
        def handle_output(self, context, _obj):
            assert context.asset_partitions_time_window == TimeWindow(
                pendulum.parse("2021-06-06"), pendulum.parse("2021-06-07")
            )

        def load_input(self, context):
            assert context.asset_partitions_time_window == TimeWindow(
                pendulum.parse("2021-06-06"), pendulum.parse("2021-06-07")
            )

    @asset(partitions_def=partitions_def)
    def upstream_asset():
        pass

    @asset(partitions_def=partitions_def)
    def downstream_asset(context, upstream_asset):
        assert context.asset_partitions_time_window_for_input("upstream_asset") == TimeWindow(
            pendulum.parse("2021-06-06"), pendulum.parse("2021-06-07")
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

    daily_job = build_assets_job(
        name="daily_job",
        assets=[daily_asset],
        source_assets=[hourly_asset],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(CustomIOManager())},
    )
    assert daily_job.execute_in_process(partition_key="2021-06-06").success


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

    daily_job = build_assets_job(
        name="daily_job",
        assets=[daily_asset],
        source_assets=[hourly_asset],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(CustomIOManager())},
    )
    assert daily_job.execute_in_process(partition_key="2021-06-06").success


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
        upstream_asset.partitions_def,
        AssetKey("upstream_asset_1"),
        PartitionKeyRange("a", "c"),
    ) == PartitionKeyRange("a", "c")

    assert get_upstream_partitions_for_partition_range(
        downstream_asset_2,
        upstream_asset.partitions_def,
        AssetKey("upstream_asset_2"),
        PartitionKeyRange("a", "c"),
    ) == PartitionKeyRange("a", "c")

    assert get_downstream_partitions_for_partition_range(
        downstream_asset_1,
        upstream_asset,
        AssetKey("upstream_asset_1"),
        PartitionKeyRange("a", "c"),
    ) == PartitionKeyRange("a", "c")

    assert get_downstream_partitions_for_partition_range(
        downstream_asset_2,
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

    my_job = build_assets_job(
        "my_job",
        assets=[my_asset],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )
    result = my_job.execute_in_process(partition_key="b")

    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("my_asset"),
        [
            AssetMaterialization(asset_key=AssetKey(["my_asset_1"]), partition="b"),
            AssetMaterialization(asset_key=AssetKey(["my_asset_2"]), partition="b"),
        ],
        exclude_fields=["tags"],
    )


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

    my_job = build_assets_job(
        "my_job", assets=[upstream_asset, downstream_asset_1, downstream_asset_2]
    )
    result = my_job.execute_in_process(partition_key="b")

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
        assert context.op_config["a"] == 5
        assert context.partition_key == "2020-01-01"

    the_job = define_asset_job(
        "job",
        partitions_def=daily_partitions_def,
        config={"ops": {"asset1": {"config": {"a": 5}}}},
    ).resolve(asset_graph=AssetGraph.from_assets([asset1]))

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
        assert context.op_config["day_of_month"] == 1
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
        assert context.op_config["day_of_month"] == 1
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


def test_partition_range_single_run():
    partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")

    @asset(partitions_def=partitions_def)
    def upstream_asset(context) -> None:
        assert context.asset_partition_key_range_for_output() == PartitionKeyRange(
            start="2020-01-01", end="2020-01-03"
        )

    @asset(partitions_def=partitions_def, non_argument_deps={"upstream_asset"})
    def downstream_asset(context) -> None:
        assert context.asset_partition_key_range_for_input("upstream_asset") == PartitionKeyRange(
            start="2020-01-01", end="2020-01-03"
        )
        assert context.asset_partition_key_range_for_output() == PartitionKeyRange(
            start="2020-01-01", end="2020-01-03"
        )

    the_job = define_asset_job("job").resolve(
        asset_graph=AssetGraph.from_assets([upstream_asset, downstream_asset])
    )

    result = the_job.execute_in_process(
        tags={
            ASSET_PARTITION_RANGE_START_TAG: "2020-01-01",
            ASSET_PARTITION_RANGE_END_TAG: "2020-01-03",
        }
    )

    assert {
        materialization.partition
        for materialization in result.asset_materializations_for_node("upstream_asset")
    } == {"2020-01-01", "2020-01-02", "2020-01-03"}
    assert {
        materialization.partition
        for materialization in result.asset_materializations_for_node("downstream_asset")
    } == {"2020-01-01", "2020-01-02", "2020-01-03"}


def test_multipartition_range_single_run():
    partitions_def = MultiPartitionsDefinition(
        {
            "date": DailyPartitionsDefinition(start_date="2020-01-01"),
            "abc": StaticPartitionsDefinition(["a", "b", "c"]),
        }
    )

    @asset(partitions_def=partitions_def)
    def multipartitioned_asset(context) -> None:
        key_range = context.asset_partition_key_range_for_output()

        assert isinstance(key_range.start, MultiPartitionKey)
        assert isinstance(key_range.end, MultiPartitionKey)
        assert key_range.start == MultiPartitionKey({"date": "2020-01-01", "abc": "a"})
        assert key_range.end == MultiPartitionKey({"date": "2020-01-03", "abc": "a"})

        assert all(
            isinstance(key, MultiPartitionKey) for key in context.asset_partition_keys_for_output()
        )

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


def test_error_on_nonexistent_upstream_partition():
    @asset(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"))
    def upstream_asset(context):
        return 1

    @asset(partitions_def=HourlyPartitionsDefinition(start_date="2020-01-01-00:00"))
    def downstream_asset(context, upstream_asset):
        return upstream_asset + 1

    with pendulum.test(create_pendulum_time(2020, 1, 2, 10, 0)):
        with pytest.raises(
            DagsterInvariantViolationError,
            match="invalid partition keys",
        ):
            materialize(
                [downstream_asset, upstream_asset.to_source_asset()],
                partition_key="2020-01-02-05:00",
            )
