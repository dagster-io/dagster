import inspect
from datetime import datetime
from typing import Optional

from dagster import (
    AllPartitionMapping,
    AssetExecutionContext,
    AssetIn,
    AssetMaterialization,
    AssetsDefinition,
    DailyPartitionsDefinition,
    IdentityPartitionMapping,
    IOManager,
    IOManagerDefinition,
    LastPartitionMapping,
    MultiPartitionKey,
    MultiPartitionsDefinition,
    MultiToSingleDimensionPartitionMapping,
    PartitionsDefinition,
    SourceAsset,
    SpecificPartitionsPartitionMapping,
    StaticPartitionsDefinition,
    TimeWindowPartitionMapping,
    WeeklyPartitionsDefinition,
    define_asset_job,
    graph,
    materialize,
    op,
)
from dagster._core.definitions import asset, build_assets_job
from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_out import AssetOut
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partition import DefaultPartitionsSubset, PartitionsSubset
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partition_mapping import (
    PartitionMapping,
    UpstreamPartitionsResult,
    get_builtin_partition_mapping_types,
)
from dagster._core.instance import DynamicPartitionsStore
from dagster._core.test_utils import assert_namedtuple_lists_equal


def test_access_partition_keys_from_context_non_identity_partition_mapping():
    upstream_partitions_def = StaticPartitionsDefinition(["1", "2", "3"])
    downstream_partitions_def = StaticPartitionsDefinition(["1", "2", "3"])

    class TrailingWindowPartitionMapping(PartitionMapping):
        """Maps each downstream partition to two partitions in the upstream asset: itself and the
        preceding partition.
        """

        def get_upstream_mapped_partitions_result_for_partitions(
            self,
            downstream_partitions_subset: Optional[PartitionsSubset],
            upstream_partitions_def: PartitionsDefinition,
            current_time: Optional[datetime] = None,
            dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
        ) -> UpstreamPartitionsResult:
            assert downstream_partitions_subset
            assert upstream_partitions_def

            partition_keys = list(downstream_partitions_subset.get_partition_keys())
            return UpstreamPartitionsResult(
                upstream_partitions_def.empty_subset().with_partition_key_range(
                    PartitionKeyRange(str(max(1, int(partition_keys[0]) - 1)), partition_keys[-1])
                ),
                [],
            )

        def get_downstream_partitions_for_partitions(
            self,
            upstream_partitions_subset: PartitionsSubset,
            downstream_partitions_def: PartitionsDefinition,
            current_time: Optional[datetime] = None,
            dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
        ) -> PartitionsSubset:
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

    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("upstream_asset"),
        [AssetMaterialization(AssetKey(["upstream_asset"]), partition="2")],
        exclude_fields=["tags"],
    )
    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("downstream_asset"),
        [AssetMaterialization(AssetKey(["downstream_asset"]), partition="2")],
        exclude_fields=["tags"],
    )


def test_from_graph():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])

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
                partition_mappings={"upstream_asset": IdentityPartitionMapping()},
            ),
        ],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )
    assert my_job.execute_in_process(partition_key="a").success


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
    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("upstream"),
        [AssetMaterialization(AssetKey(["upstream"]), partition="b")],
        exclude_fields=["tags"],
    )
    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("downstream"),
        [AssetMaterialization(AssetKey(["downstream"]))],
        exclude_fields=["tags"],
    )


def test_non_partitioned_depends_on_specific_partitions():
    @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c", "d"]))
    def upstream():
        pass

    @asset(
        ins={"upstream": AssetIn(partition_mapping=SpecificPartitionsPartitionMapping(["a", "b"]))}
    )
    def downstream_a_b(upstream):
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
            assert set(context.asset_partition_keys) == {"a", "b"}

    result = materialize(
        [upstream, downstream_a_b],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key="b",
    )
    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("upstream"),
        [AssetMaterialization(AssetKey(["upstream"]), partition="b")],
        exclude_fields=["tags"],
    )
    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("downstream"),
        [AssetMaterialization(AssetKey(["downstream_a_b"]))],
        exclude_fields=["tags"],
    )


def test_specific_partitions_partition_mapping_downstream_partitions():
    upstream_partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])
    downstream_partitions_def = StaticPartitionsDefinition(["x", "y", "z"])
    partition_mapping = SpecificPartitionsPartitionMapping(["a", "b"])

    # cases where at least one of the specific partitions is in the upstream partitions subset
    for partition_subset in [
        DefaultPartitionsSubset(upstream_partitions_def, {"a"}),
        DefaultPartitionsSubset(upstream_partitions_def, {"a", "b"}),
        DefaultPartitionsSubset(upstream_partitions_def, {"a", "b", "c", "d"}),
    ]:
        assert (
            partition_mapping.get_downstream_partitions_for_partitions(
                partition_subset, downstream_partitions_def
            )
            == downstream_partitions_def.subset_with_all_partitions()
        )

    for partition_subset in [
        DefaultPartitionsSubset(upstream_partitions_def, {"c"}),
        DefaultPartitionsSubset(upstream_partitions_def, {"c", "d"}),
    ]:
        assert (
            partition_mapping.get_downstream_partitions_for_partitions(
                partition_subset, downstream_partitions_def
            )
            == downstream_partitions_def.empty_subset()
        )


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
    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("upstream"),
        [AssetMaterialization(AssetKey(["upstream"]), partition="b")],
        exclude_fields=["tags"],
    )
    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("downstream"),
        [AssetMaterialization(AssetKey(["downstream"]))],
        exclude_fields=["tags"],
    )


def test_partition_keys_in_range():
    daily_partition_keys_for_week_2022_09_11 = [
        "2022-09-11",
        "2022-09-12",
        "2022-09-13",
        "2022-09-14",
        "2022-09-15",
        "2022-09-16",
        "2022-09-17",
    ]

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2022-09-11"))
    def upstream(context):
        assert context.asset_partition_keys_for_output("result") == ["2022-09-11"]
        assert context.asset_partition_keys_for_output() == ["2022-09-11"]

    @asset(partitions_def=WeeklyPartitionsDefinition(start_date="2022-09-11"))
    def downstream(context, upstream):
        assert (
            context.asset_partition_keys_for_input("upstream")
            == daily_partition_keys_for_week_2022_09_11
        )

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            if context.asset_key == AssetKey("upstream"):
                assert context.has_asset_partitions
                assert context.asset_partition_keys == ["2022-09-11"]

        def load_input(self, context):
            assert context.has_asset_partitions
            assert context.asset_partition_keys == daily_partition_keys_for_week_2022_09_11

    upstream_job = build_assets_job(
        "upstream_job",
        assets=[upstream],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )
    upstream_job.execute_in_process(partition_key="2022-09-11")

    downstream_job = build_assets_job(
        "downstream_job",
        assets=[downstream],
        source_assets=[upstream],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )
    downstream_job.execute_in_process(partition_key="2022-09-11")


def test_dependency_resolution_partition_mapping():
    @asset(
        partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
        key_prefix=["staging"],
    )
    def upstream(context):
        partition_date_str = context.asset_partition_key_for_output()
        return partition_date_str

    @asset(
        partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
        key_prefix=["staging"],
        ins={
            "upstream": AssetIn(
                partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=0),
            )
        },
    )
    def downstream(context, upstream):
        context.log.info(upstream)
        return upstream

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            ...

        def load_input(self, context):
            assert context.asset_key.path == ["staging", "upstream"]
            assert context.partition_key == "2020-01-02"
            assert context.asset_partition_keys == ["2020-01-01", "2020-01-02"]

    materialize(
        [upstream, downstream], resources={"io_manager": MyIOManager()}, partition_key="2020-01-02"
    )


def test_exported_partition_mappings_whitelisted():
    import dagster

    dagster_exports = (getattr(dagster, attr_name) for attr_name in dagster.__dir__())

    exported_partition_mapping_classes = {
        export
        for export in dagster_exports
        if inspect.isclass(export) and issubclass(export, PartitionMapping)
    } - {PartitionMapping}

    assert set(get_builtin_partition_mapping_types()) == exported_partition_mapping_classes


def test_multipartitions_def_partition_mapping_infer_identity():
    composite = MultiPartitionsDefinition(
        {
            "abc": StaticPartitionsDefinition(["a", "b", "c"]),
            "123": StaticPartitionsDefinition(["1", "2", "3"]),
        }
    )

    @asset(partitions_def=composite)
    def upstream(context):
        return 1

    @asset(partitions_def=composite)
    def downstream(context, upstream):
        assert (
            context.asset_partition_keys_for_input("upstream")
            == context.asset_partition_keys_for_output()
        )
        return 1

    asset_graph = AssetGraph.from_assets([upstream, downstream])
    assets_job = define_asset_job("foo", [upstream, downstream]).resolve(asset_graph=asset_graph)

    assert (
        asset_graph.get_partition_mapping(upstream.key, downstream.key)
        == IdentityPartitionMapping()
    )
    assert assets_job.execute_in_process(
        partition_key=MultiPartitionKey({"abc": "a", "123": "1"})
    ).success


def test_multipartitions_def_partition_mapping_infer_single_dim_to_multi():
    abc_def = StaticPartitionsDefinition(["a", "b", "c"])

    composite = MultiPartitionsDefinition(
        {
            "abc": abc_def,
            "123": StaticPartitionsDefinition(["1", "2", "3"]),
        }
    )

    @asset(partitions_def=abc_def)
    def upstream(context):
        assert context.asset_partition_keys_for_output("result") == ["a"]
        return 1

    @asset(partitions_def=composite)
    def downstream(context, upstream):
        assert context.asset_partition_keys_for_input("upstream") == ["a"]
        assert context.asset_partition_keys_for_output("result") == [
            MultiPartitionKey({"abc": "a", "123": "1"})
        ]
        return 1

    asset_graph = AssetGraph.from_assets([upstream, downstream])

    assert (
        asset_graph.get_partition_mapping(upstream.key, downstream.key)
        == MultiToSingleDimensionPartitionMapping()
    )

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            if context.asset_key == AssetKey("upstream"):
                assert context.has_asset_partitions
                assert context.asset_partition_keys == ["a"]

        def load_input(self, context):
            assert context.has_asset_partitions
            assert context.asset_partition_keys == ["a"]

    materialize(
        [upstream],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key="a",
    )

    materialize(
        [downstream, SourceAsset(AssetKey("upstream"), partitions_def=abc_def)],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key=MultiPartitionKey({"abc": "a", "123": "1"}),
    )


def test_multipartitions_def_partition_mapping_infer_multi_to_single_dim():
    abc_def = StaticPartitionsDefinition(["a", "b", "c"])

    composite = MultiPartitionsDefinition(
        {
            "abc": abc_def,
            "123": StaticPartitionsDefinition(["1", "2", "3"]),
        }
    )

    a_multipartition_keys = {
        MultiPartitionKey(kv)
        for kv in [{"abc": "a", "123": "1"}, {"abc": "a", "123": "2"}, {"abc": "a", "123": "3"}]
    }

    @asset(partitions_def=composite)
    def upstream(context):
        return 1

    @asset(partitions_def=abc_def)
    def downstream(context, upstream):
        assert set(context.asset_partition_keys_for_input("upstream")) == a_multipartition_keys
        assert context.asset_partition_keys_for_output("result") == ["a"]
        return 1

    asset_graph = AssetGraph.from_assets([upstream, downstream])

    assert (
        asset_graph.get_partition_mapping(upstream.key, downstream.key)
        == MultiToSingleDimensionPartitionMapping()
    )

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert set(context.asset_partition_keys) == a_multipartition_keys

    for pk in a_multipartition_keys:
        materialize(
            [upstream],
            resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
            partition_key=pk,
        )

    materialize(
        [downstream, SourceAsset(AssetKey("upstream"), partitions_def=composite)],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key="a",
    )


def test_identity_partition_mapping():
    xy = StaticPartitionsDefinition(["x", "y"])
    zx = StaticPartitionsDefinition(["z", "x"])

    result = IdentityPartitionMapping().get_upstream_mapped_partitions_result_for_partitions(
        zx.empty_subset().with_partition_keys(["z", "x"]), xy
    )
    assert result.partitions_subset.get_partition_keys() == set(["x"])
    assert result.required_but_nonexistent_partition_keys == ["z"]

    result = IdentityPartitionMapping().get_downstream_partitions_for_partitions(
        zx.empty_subset().with_partition_keys(["z", "x"]), xy
    )
    assert result.get_partition_keys() == set(["x"])


def test_partition_mapping_with_outputs():
    class TestIOManager(IOManager):
        def handle_output(self, context, obj) -> None:
            return None

        def load_input(self, context):
            return 1

    @multi_asset(
        outs={"asset_1": AssetOut(), "asset_2": AssetOut()},
        partitions_def=DailyPartitionsDefinition(start_date="2023-08-15"),
    )
    def multi_asset_1():
        return

    @multi_asset(
        outs={"asset_1": AssetOut(), "asset_2": AssetOut()},
        ins={
            "asset_1": AssetIn(
                partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
            ),
            "asset_2": AssetIn(
                partition_mapping=TimeWindowPartitionMapping(start_offset=-2, end_offset=-2)
            ),
        },
        partitions_def=DailyPartitionsDefinition(start_date="2023-08-15"),
    )
    def multi_asset_2(context: AssetExecutionContext, asset_1, asset_2):
        context.asset_partition_key_for_input("asset_1")
        return

    materialize(
        [multi_asset_2], partition_key="2023-08-20", resources={"io_manager": TestIOManager()}
    )


def test_partition_mapping_with_asset_deps():
    asset_1 = AssetSpec(asset_key="asset_1")
    asset_2 = AssetSpec(asset_key="asset_2")
    asset_3 = AssetSpec(
        asset_key="asset_3",
        deps=[
            AssetDep(
                asset=asset_1,
                partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
            ),
            AssetDep(
                asset=asset_2,
                partition_mapping=TimeWindowPartitionMapping(start_offset=-2, end_offset=-2),
            ),
        ],
    )
    asset_4 = AssetSpec(
        asset_key="asset_4",
        deps=[
            AssetDep(
                asset=asset_1,
                partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
            ),
            AssetDep(
                asset=asset_2,
                partition_mapping=TimeWindowPartitionMapping(start_offset=-2, end_offset=-2),
            ),
        ],
    )

    @multi_asset(
        specs=[asset_1, asset_2], partitions_def=DailyPartitionsDefinition(start_date="2023-08-15")
    )
    def multi_asset_1():
        return

    @multi_asset(
        specs=[asset_3, asset_4], partitions_def=DailyPartitionsDefinition(start_date="2023-08-15")
    )
    def multi_asset_2(context: AssetExecutionContext):
        context.asset_partition_key_for_input("asset_1")
        # this call is failing unless multi_asset_1 is in the materialize call. Otherwise the asset
        # asset_1 isn't in the AssetLayer

        # but in the Outs case, we dont need multi_asset_1 in the materialize call for asset_1 to be in
        # the AssetLayer
        return

    materialize([multi_asset_1, multi_asset_2], partition_key="2023-08-20")
