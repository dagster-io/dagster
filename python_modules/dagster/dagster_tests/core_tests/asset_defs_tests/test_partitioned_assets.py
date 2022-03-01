import pendulum
import pytest

from dagster import (
    AssetMaterialization,
    DagsterInvalidDefinitionError,
    DailyPartitionsDefinition,
    IOManager,
    IOManagerDefinition,
    PartitionsDefinition,
    StaticPartitionsDefinition,
)
from dagster.core.asset_defs import asset, build_assets_job
from dagster.core.asset_defs.asset_partitions import (
    get_downstream_partitions_for_partition_range,
    get_upstream_partitions_for_partition_range,
)
from dagster.core.asset_defs.partition_mapping import PartitionMapping
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.partition_key_range import PartitionKeyRange
from dagster.core.definitions.time_window_partitions import TimeWindow


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
        upstream_asset,
        AssetKey("upstream_asset"),
        PartitionKeyRange("a", "c"),
    ) == PartitionKeyRange("a", "c")

    assert get_downstream_partitions_for_partition_range(
        downstream_asset,
        upstream_asset,
        AssetKey("upstream_asset"),
        PartitionKeyRange("a", "c"),
    ) == PartitionKeyRange("a", "c")


def test_filter_mapping_partitions_dep():
    downstream_partitions = ["john", "ringo", "paul", "george"]
    upstream_partitions = [
        f"{hemisphere}|{beatle}"
        for beatle in downstream_partitions
        for hemisphere in ["southern", "northern"]
    ]
    downstream_partitions_def = StaticPartitionsDefinition(downstream_partitions)
    upstream_partitions_def = StaticPartitionsDefinition(upstream_partitions)

    class HemisphereFilteringPartitionMapping(PartitionMapping):
        def __init__(self, hemisphere: str):
            self.hemisphere = hemisphere

        def get_upstream_partitions_for_partition_range(
            self,
            downstream_partition_key_range: PartitionKeyRange,
            downstream_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
            upstream_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
        ) -> PartitionKeyRange:
            return PartitionKeyRange(
                f"{self.hemisphere}|{downstream_partition_key_range.start}",
                f"{self.hemisphere}|{downstream_partition_key_range.end}",
            )

        def get_downstream_partitions_for_partition_range(
            self,
            upstream_partition_key_range: PartitionKeyRange,
            downstream_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
            upstream_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
        ) -> PartitionKeyRange:
            return PartitionKeyRange(
                upstream_partition_key_range.start.split("|")[-1],
                upstream_partition_key_range.end.split("|")[-1],
            )

    @asset(partitions_def=upstream_partitions_def)
    def upstream_asset():
        pass

    @asset(
        partitions_def=downstream_partitions_def,
        partition_mappings={"upstream_asset": HemisphereFilteringPartitionMapping("southern")},
    )
    def downstream_asset(upstream_asset):
        assert upstream_asset

    assert get_upstream_partitions_for_partition_range(
        downstream_asset,
        upstream_asset,
        AssetKey("upstream_asset"),
        PartitionKeyRange("ringo", "paul"),
    ) == PartitionKeyRange("southern|ringo", "southern|paul")

    assert get_downstream_partitions_for_partition_range(
        downstream_asset,
        upstream_asset,
        AssetKey("upstream_asset"),
        PartitionKeyRange("southern|ringo", "southern|paul"),
    ) == PartitionKeyRange("ringo", "paul")


def test_single_partitioned_asset_job():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert context.asset_partition_key == "b"

        def load_input(self, context):
            assert False, "shouldn't get here"

    @asset(partitions_def=partitions_def)
    def my_asset():
        pass

    my_job = build_assets_job(
        "my_job",
        assets=[my_asset],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )
    result = my_job.execute_in_process(partition_key="b")
    assert result.asset_materializations_for_node("my_asset") == [
        AssetMaterialization(asset_key=AssetKey(["my_asset"]), partition="b")
    ]


def test_two_partitioned_assets_job():
    @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c", "d"]))
    def upstream():
        pass

    @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c", "d"]))
    def downstream(upstream):
        assert upstream is None

    my_job = build_assets_job("my_job", assets=[upstream, downstream])
    result = my_job.execute_in_process(partition_key="b")
    assert result.asset_materializations_for_node("upstream") == [
        AssetMaterialization(AssetKey(["upstream"]), partition="b")
    ]
    assert result.asset_materializations_for_node("downstream") == [
        AssetMaterialization(AssetKey(["downstream"]), partition="b")
    ]


def test_assets_job_with_different_partitions_defs():
    with pytest.raises(DagsterInvalidDefinitionError):

        @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c"]))
        def upstream():
            pass

        @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c", "d"]))
        def downstream(upstream):
            assert upstream is None

        build_assets_job("my_job", assets=[upstream, downstream])


def test_access_partition_keys_from_context_non_identity_partition_mapping():
    upstream_partitions_def = StaticPartitionsDefinition(["1", "2", "3"])
    downstream_partitions_def = StaticPartitionsDefinition(["1", "2", "3"])

    class TrailingWindowPartitionMapping(PartitionMapping):
        """
        Maps each downstream partition to two partitions in the upstream asset: itself and the
        preceding partition.
        """

        def get_upstream_partitions_for_partition_range(
            self,
            downstream_partition_key_range: PartitionKeyRange,
            downstream_partitions_def: PartitionsDefinition,
            upstream_partitions_def: PartitionsDefinition,
        ) -> PartitionKeyRange:
            assert downstream_partitions_def
            assert upstream_partitions_def

            start, end = downstream_partition_key_range
            return PartitionKeyRange(str(max(1, int(start) - 1)), end)

        def get_downstream_partitions_for_partition_range(
            self,
            upstream_partition_key_range: PartitionKeyRange,
            downstream_partitions_def: PartitionsDefinition,
            upstream_partitions_def: PartitionsDefinition,
        ) -> PartitionKeyRange:
            raise NotImplementedError()

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert context.asset_partition_key == "2"

        def load_input(self, context):
            start, end = context.asset_partition_key_range
            assert start, end == ("1", "2")

    @asset(partitions_def=upstream_partitions_def)
    def upstream_asset(context):
        assert context.output_asset_partition_key() == "2"

    @asset(
        partitions_def=downstream_partitions_def,
        partition_mappings={"upstream_asset": TrailingWindowPartitionMapping()},
    )
    def downstream_asset(context, upstream_asset):
        assert context.output_asset_partition_key() == "2"
        assert upstream_asset is None

    my_job = build_assets_job(
        "my_job",
        assets=[upstream_asset, downstream_asset],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )
    result = my_job.execute_in_process(partition_key="2")
    assert result.asset_materializations_for_node("upstream_asset") == [
        AssetMaterialization(AssetKey(["upstream_asset"]), partition="2")
    ]
    assert result.asset_materializations_for_node("downstream_asset") == [
        AssetMaterialization(AssetKey(["downstream_asset"]), partition="2")
    ]


def test_access_partition_keys_from_context_only_one_asset_partitioned():
    upstream_partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            if context.op_def.name == "upstream_asset":
                assert context.asset_partition_key == "b"
            elif context.op_def.name == "downstream_asset":
                assert not context.has_asset_partitions
                with pytest.raises(Exception):  # TODO: better error message
                    assert context.asset_partition_key_range
            else:
                assert False

        def load_input(self, context):
            assert not context.has_asset_partitions

    @asset(partitions_def=upstream_partitions_def)
    def upstream_asset(context):
        assert context.output_asset_partition_key() == "b"

    @asset
    def downstream_asset(upstream_asset):
        assert upstream_asset is None

    my_job = build_assets_job(
        "my_job",
        assets=[upstream_asset, downstream_asset],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )
    result = my_job.execute_in_process(partition_key="b")
    assert result.asset_materializations_for_node("upstream_asset") == [
        AssetMaterialization(asset_key=AssetKey(["upstream_asset"]), partition="b")
    ]


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
    def downstream_asset(upstream_asset):
        assert upstream_asset is None

    my_job = build_assets_job(
        "my_job",
        assets=[downstream_asset, upstream_asset],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )
    my_job.execute_in_process(partition_key="2021-06-06")


def test_asset_partitions_time_window_non_identity_partition_mapping():
    upstream_partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")
    downstream_partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")

    class TrailingWindowPartitionMapping(PartitionMapping):
        """
        Maps each downstream partition to two partitions in the upstream asset: itself and the
        preceding partition.
        """

        def get_upstream_partitions_for_partition_range(
            self,
            downstream_partition_key_range: PartitionKeyRange,
            downstream_partitions_def: PartitionsDefinition,
            upstream_partitions_def: PartitionsDefinition,
        ) -> PartitionKeyRange:
            del downstream_partitions_def, upstream_partitions_def

            start, end = downstream_partition_key_range
            assert start == "2020-01-02"
            assert end == "2020-01-02"
            return PartitionKeyRange("2020-01-01", "2020-01-02")

        def get_downstream_partitions_for_partition_range(
            self,
            upstream_partition_key_range: PartitionKeyRange,
            downstream_partitions_def: PartitionsDefinition,
            upstream_partitions_def: PartitionsDefinition,
        ) -> PartitionKeyRange:
            raise NotImplementedError()

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert context.asset_partitions_time_window == TimeWindow(
                pendulum.parse("2020-01-02"), pendulum.parse("2020-01-03")
            )

        def load_input(self, context):
            assert context.asset_partitions_time_window == TimeWindow(
                pendulum.parse("2020-01-01"), pendulum.parse("2020-01-03")
            )

    @asset(partitions_def=upstream_partitions_def)
    def upstream_asset():
        pass

    @asset(
        partitions_def=downstream_partitions_def,
        partition_mappings={"upstream_asset": TrailingWindowPartitionMapping()},
    )
    def downstream_asset(upstream_asset):
        assert upstream_asset is None

    my_job = build_assets_job(
        "my_job",
        assets=[upstream_asset, downstream_asset],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )
    my_job.execute_in_process(partition_key="2020-01-02")
