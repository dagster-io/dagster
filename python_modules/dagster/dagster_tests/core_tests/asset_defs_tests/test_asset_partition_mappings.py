from typing import Optional

import pendulum

from dagster import (
    AllPartitionMapping,
    AssetIn,
    AssetMaterialization,
    AssetsDefinition,
    DailyPartitionsDefinition,
    IOManager,
    IOManagerDefinition,
    LastPartitionMapping,
    Out,
    Output,
    PartitionsDefinition,
    StaticPartitionsDefinition,
    graph,
    op,
)
from dagster._core.definitions import asset, build_assets_job, multi_asset
from dagster._core.definitions.asset_partitions import (
    get_downstream_partitions_for_partition_range,
    get_upstream_partitions_for_partition_range,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partition_mapping import PartitionMapping
from dagster._core.definitions.time_window_partitions import TimeWindow


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
            downstream_partition_key_range,
            downstream_partitions_def: Optional[
                PartitionsDefinition
            ],  # pylint: disable=unused-argument
            upstream_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
        ) -> PartitionKeyRange:
            return PartitionKeyRange(
                f"{self.hemisphere}|{downstream_partition_key_range.start}",
                f"{self.hemisphere}|{downstream_partition_key_range.end}",
            )

        def get_downstream_partitions_for_partition_range(
            self,
            upstream_partition_key_range: PartitionKeyRange,
            downstream_partitions_def: Optional[
                PartitionsDefinition
            ],  # pylint: disable=unused-argument
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
        ins={
            "upstream_asset": AssetIn(
                partition_mapping=HemisphereFilteringPartitionMapping("southern")
            )
        },
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
            downstream_partition_key_range,
            downstream_partitions_def: Optional[PartitionsDefinition],
            upstream_partitions_def: PartitionsDefinition,
        ) -> PartitionKeyRange:
            assert downstream_partitions_def
            assert upstream_partitions_def

            start, end = downstream_partition_key_range
            return PartitionKeyRange(str(max(1, int(start) - 1)), end)

        def get_downstream_partitions_for_partition_range(
            self,
            upstream_partition_key_range: PartitionKeyRange,
            downstream_partitions_def: Optional[PartitionsDefinition],
            upstream_partitions_def: PartitionsDefinition,
        ) -> PartitionKeyRange:
            raise NotImplementedError()

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert context.asset_partition_key == "2"

        def load_input(self, context):
            start, end = context.asset_partition_key_range
            assert start, end == ("1", "2")
            assert context.asset_partitions_def == upstream_partitions_def

    @asset(partitions_def=upstream_partitions_def)
    def upstream_asset(context):
        assert context.asset_partition_key_for_output() == "2"

    @asset(
        partitions_def=downstream_partitions_def,
        ins={"upstream_asset": AssetIn(partition_mapping=TrailingWindowPartitionMapping())},
    )
    def downstream_asset(context, upstream_asset):
        assert context.asset_partition_key_for_output() == "2"
        assert upstream_asset is None
        assert context.asset_partitions_def_for_input("upstream_asset") == upstream_partitions_def

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
            downstream_partition_key_range,
            downstream_partitions_def: Optional[PartitionsDefinition],
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
            downstream_partitions_def: Optional[PartitionsDefinition],
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
        ins={"upstream_asset": AssetIn(partition_mapping=TrailingWindowPartitionMapping())},
    )
    def downstream_asset(upstream_asset):
        assert upstream_asset is None

    my_job = build_assets_job(
        "my_job",
        assets=[upstream_asset, downstream_asset],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )
    my_job.execute_in_process(partition_key="2020-01-02")


def test_multi_asset_non_identity_partition_mapping():
    upstream_partitions_def = StaticPartitionsDefinition(["1", "2", "3"])
    downstream_partitions_def = StaticPartitionsDefinition(["1", "2", "3"])

    class TrailingWindowPartitionMapping(PartitionMapping):
        """
        Maps each downstream partition to two partitions in the upstream asset: itself and the
        preceding partition.
        """

        def get_upstream_partitions_for_partition_range(
            self,
            downstream_partition_key_range,
            downstream_partitions_def: Optional[PartitionsDefinition],
            upstream_partitions_def: PartitionsDefinition,
        ) -> PartitionKeyRange:
            assert downstream_partitions_def
            assert upstream_partitions_def

            start, end = downstream_partition_key_range
            return PartitionKeyRange(str(max(1, int(start) - 1)), end)

        def get_downstream_partitions_for_partition_range(
            self,
            upstream_partition_key_range: PartitionKeyRange,
            downstream_partitions_def: Optional[PartitionsDefinition],
            upstream_partitions_def: PartitionsDefinition,
        ) -> PartitionKeyRange:
            raise NotImplementedError()

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert context.asset_partition_key == "2"

        def load_input(self, context):
            start, end = context.asset_partition_key_range
            assert start, end == ("1", "2")

    @multi_asset(
        outs={
            "out1": Out(asset_key=AssetKey("upstream_asset_1")),
            "out2": Out(asset_key=AssetKey("upstream_asset_2")),
        },
        partitions_def=upstream_partitions_def,
    )
    def upstream_asset(context):
        assert context.asset_partition_key_for_output("out1") == "2"
        assert context.asset_partition_key_for_output("out2") == "2"
        return (Output(1, output_name="out1"), Output(2, output_name="out2"))

    @asset(
        partitions_def=downstream_partitions_def,
        ins={"upstream_asset_1": AssetIn(partition_mapping=TrailingWindowPartitionMapping())},
    )
    def downstream_asset_1(context, upstream_asset_1):
        assert context.asset_partition_key_for_output() == "2"
        assert upstream_asset_1 is None

    @asset(
        partitions_def=downstream_partitions_def,
        ins={"upstream_asset_2": AssetIn(partition_mapping=TrailingWindowPartitionMapping())},
    )
    def downstream_asset_2(context, upstream_asset_2):
        assert context.asset_partition_key_for_output() == "2"
        assert upstream_asset_2 is None

    my_job = build_assets_job(
        "my_job",
        assets=[upstream_asset, downstream_asset_1, downstream_asset_2],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )
    result = my_job.execute_in_process(partition_key="2")
    assert result.asset_materializations_for_node("upstream_asset") == [
        AssetMaterialization(AssetKey(["upstream_asset_1"]), partition="2"),
        AssetMaterialization(AssetKey(["upstream_asset_2"]), partition="2"),
    ]
    assert result.asset_materializations_for_node("downstream_asset_1") == [
        AssetMaterialization(AssetKey(["downstream_asset_1"]), partition="2")
    ]
    assert result.asset_materializations_for_node("downstream_asset_2") == [
        AssetMaterialization(AssetKey(["downstream_asset_2"]), partition="2")
    ]


def test_from_graph():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])

    class SpecialIdentityPartitionMapping(PartitionMapping):
        def __init__(self):
            self.upstream_calls = 0
            self.downstream_calls = 0

        def get_upstream_partitions_for_partition_range(
            self,
            downstream_partition_key_range,
            downstream_partitions_def: Optional[
                PartitionsDefinition
            ],  # pylint: disable=unused-argument
            upstream_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
        ) -> PartitionKeyRange:
            self.upstream_calls += 1
            return downstream_partition_key_range

        def get_downstream_partitions_for_partition_range(
            self,
            upstream_partition_key_range: PartitionKeyRange,
            downstream_partitions_def: Optional[
                PartitionsDefinition
            ],  # pylint: disable=unused-argument
            upstream_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
        ) -> PartitionKeyRange:
            self.downstream_calls += 1
            return upstream_partition_key_range

    partition_mapping = SpecialIdentityPartitionMapping()

    @op
    def my_op(context):
        assert context.asset_partition_key_for_output() == "a"

    @graph
    def upstream_asset():
        return my_op()

    @op
    def my_op2(context, upstream_asset):
        assert context.asset_partition_key_for_input("upstream_asset") == "a"
        assert context.asset_partition_key_for_output() == "a"
        return upstream_asset

    @graph
    def downstream_asset(upstream_asset):
        return my_op2(upstream_asset)

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert context.asset_partition_key == "a"
            assert context.has_asset_partitions

        def load_input(self, context):
            assert context.asset_partition_key == "a"
            assert context.has_asset_partitions

    my_job = build_assets_job(
        "my_job",
        assets=[
            AssetsDefinition.from_graph(upstream_asset, partitions_def=partitions_def),
            AssetsDefinition.from_graph(
                downstream_asset,
                partitions_def=partitions_def,
                partition_mappings={"upstream_asset": partition_mapping},
            ),
        ],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )
    assert my_job.execute_in_process(partition_key="a").success
    assert partition_mapping.downstream_calls == 0
    assert partition_mapping.upstream_calls == 2


def test_non_partitioned_depends_on_last_partition():
    @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c", "d"]))
    def upstream():
        pass

    @asset(ins={"upstream": AssetIn(partition_mapping=LastPartitionMapping())})
    def downstream(upstream):
        assert upstream is None

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            if context.asset_key == AssetKey("upstream"):
                assert context.has_asset_partitions
                assert context.asset_partition_key == "b"
            else:
                assert not context.has_asset_partitions

        def load_input(self, context):
            assert context.has_asset_partitions
            assert context.asset_partition_key == "d"

    my_job = build_assets_job(
        "my_job",
        assets=[upstream, downstream],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )
    result = my_job.execute_in_process(partition_key="b")
    assert result.asset_materializations_for_node("upstream") == [
        AssetMaterialization(AssetKey(["upstream"]), partition="b")
    ]
    assert result.asset_materializations_for_node("downstream") == [
        AssetMaterialization(AssetKey(["downstream"]))
    ]


def test_non_partitioned_depends_on_all_partitions():
    @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c", "d"]))
    def upstream():
        pass

    @asset(ins={"upstream": AssetIn(partition_mapping=AllPartitionMapping())})
    def downstream(upstream):
        assert upstream is None

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            if context.asset_key == AssetKey("upstream"):
                assert context.has_asset_partitions
                assert context.asset_partition_key == "b"
            else:
                assert not context.has_asset_partitions

        def load_input(self, context):
            assert context.has_asset_partitions
            assert context.asset_partition_key_range == PartitionKeyRange("a", "d")

    my_job = build_assets_job(
        "my_job",
        assets=[upstream, downstream],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )
    result = my_job.execute_in_process(partition_key="b")
    assert result.asset_materializations_for_node("upstream") == [
        AssetMaterialization(AssetKey(["upstream"]), partition="b")
    ]
    assert result.asset_materializations_for_node("downstream") == [
        AssetMaterialization(AssetKey(["downstream"]))
    ]
