import inspect
from datetime import datetime, timedelta

import dagster as dg
import pytest
from dagster import (
    AssetExecutionContext,
    AssetsDefinition,
    DagsterInstance,
    Definitions,
    IOManagerDefinition,
    PartitionsDefinition,
)
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.definitions.assets.graph.asset_graph import AssetGraph
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.partitions.mapping import UpstreamPartitionsResult
from dagster._core.definitions.partitions.subset import DefaultPartitionsSubset, PartitionsSubset
from dagster._core.definitions.partitions.utils import get_builtin_partition_mapping_types
from dagster._core.instance import DynamicPartitionsStore
from dagster._core.test_utils import assert_namedtuple_lists_equal
from dagster._time import create_datetime


def test_access_partition_keys_from_context_non_identity_partition_mapping():
    upstream_partitions_def = dg.StaticPartitionsDefinition(["1", "2", "3"])
    downstream_partitions_def = dg.StaticPartitionsDefinition(["1", "2", "3"])

    class TrailingWindowPartitionMapping(dg.PartitionMapping):
        """Maps each downstream partition to two partitions in the upstream asset: itself and the
        preceding partition.
        """

        def get_upstream_mapped_partitions_result_for_partitions(
            self,
            downstream_partitions_subset: PartitionsSubset | None,
            downstream_partitions_def: dg.PartitionsDefinition | None,
            upstream_partitions_def: PartitionsDefinition,
            current_time: datetime | None = None,
            dynamic_partitions_store: DynamicPartitionsStore | None = None,
        ) -> UpstreamPartitionsResult:
            assert downstream_partitions_subset
            assert upstream_partitions_def

            partition_keys = list(downstream_partitions_subset.get_partition_keys())
            return UpstreamPartitionsResult(
                partitions_subset=upstream_partitions_def.empty_subset().with_partition_key_range(
                    upstream_partitions_def,
                    dg.PartitionKeyRange(
                        str(max(1, int(partition_keys[0]) - 1)), partition_keys[-1]
                    ),
                ),
                required_but_nonexistent_subset=upstream_partitions_def.empty_subset(),
            )

        def validate_partition_mapping(
            self,
            upstream_partitions_def: PartitionsDefinition,
            downstream_partitions_def: dg.PartitionsDefinition | None,
        ):
            pass

        def get_downstream_partitions_for_partitions(
            self,
            upstream_partitions_subset: PartitionsSubset,
            upstream_partitions_def: PartitionsDefinition,
            downstream_partitions_def: PartitionsDefinition,
            current_time: datetime | None = None,
            dynamic_partitions_store: DynamicPartitionsStore | None = None,
        ) -> PartitionsSubset:
            raise NotImplementedError()

        @property
        def description(self) -> str:
            raise NotImplementedError()

    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            assert context.asset_partition_key == "2"

        def load_input(self, context):
            start, end = context.asset_partition_key_range
            assert start, end == ("1", "2")
            assert context.asset_partitions_def == upstream_partitions_def

    @dg.asset(partitions_def=upstream_partitions_def)
    def upstream_asset(context: AssetExecutionContext):
        assert context.partition_key == "2"

    @dg.asset(
        partitions_def=downstream_partitions_def,
        ins={"upstream_asset": dg.AssetIn(partition_mapping=TrailingWindowPartitionMapping())},
    )
    def downstream_asset(context: AssetExecutionContext, upstream_asset):
        assert context.partition_key == "2"
        assert upstream_asset is None
        assert context.asset_partitions_def_for_input("upstream_asset") == upstream_partitions_def

    result = dg.materialize(
        assets=[upstream_asset, downstream_asset],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key="2",
    )

    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("upstream_asset"),
        [dg.AssetMaterialization(dg.AssetKey(["upstream_asset"]), partition="2")],
        exclude_fields=["tags"],
    )
    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("downstream_asset"),
        [dg.AssetMaterialization(dg.AssetKey(["downstream_asset"]), partition="2")],
        exclude_fields=["tags"],
    )


def test_from_graph():
    partitions_def = dg.StaticPartitionsDefinition(["a", "b", "c", "d"])

    @dg.op
    def my_op(context):
        assert context.asset_partition_key_for_output() == "a"

    @dg.graph
    def upstream_asset():
        return my_op()

    @dg.op
    def my_op2(context, upstream_asset):
        assert context.asset_partition_key_for_input("upstream_asset") == "a"
        assert context.asset_partition_key_for_output() == "a"
        return upstream_asset

    @dg.graph
    def downstream_asset(upstream_asset):
        return my_op2(upstream_asset)

    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            assert context.asset_partition_key == "a"
            assert context.has_asset_partitions

        def load_input(self, context):
            assert context.asset_partition_key == "a"
            assert context.has_asset_partitions

    assert dg.materialize(
        assets=[
            AssetsDefinition.from_graph(upstream_asset, partitions_def=partitions_def),
            AssetsDefinition.from_graph(
                downstream_asset,
                partitions_def=partitions_def,
                partition_mappings={"upstream_asset": dg.IdentityPartitionMapping()},
            ),
        ],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key="a",
    ).success


def test_downstream_identity_mapping_between_time_window_partitions():
    @dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2025-02-01", end_offset=1))
    def asset1():
        pass

    @dg.asset(
        partitions_def=dg.DailyPartitionsDefinition(start_date="2025-02-01", end_offset=0),
        ins={"asset1": dg.AssetIn(partition_mapping=dg.IdentityPartitionMapping())},
    )
    def asset2(asset1):
        pass

    defs = dg.Definitions(assets=[asset1, asset2])

    with DagsterInstance.ephemeral() as instance:
        asset_graph_view = AssetGraphView.for_test(
            defs, instance, effective_dt=create_datetime(2025, 2, 6)
        )

        # at midnight on 2025-02-06, 2025-02-06 exists on parent asset but not on child asset
        parent_subset = asset_graph_view.get_asset_subset_from_asset_partitions(
            asset1.key,
            {
                AssetKeyPartitionKey(asset1.key, "2025-02-05"),
                AssetKeyPartitionKey(asset1.key, "2025-02-06"),
            },
        )

        child_subset = asset_graph_view.compute_child_subset(asset2.key, parent_subset)

        assert child_subset.expensively_compute_asset_partitions() == {
            AssetKeyPartitionKey(asset2.key, "2025-02-05"),
        }


def test_upstream_identity_mapping_between_time_window_partitions():
    @dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2025-02-01", end_offset=0))
    def asset1():
        pass

    @dg.asset(
        partitions_def=dg.DailyPartitionsDefinition(start_date="2025-02-01", end_offset=1),
        ins={"asset1": dg.AssetIn(partition_mapping=dg.IdentityPartitionMapping())},
    )
    def asset2(asset1):
        pass

    defs = dg.Definitions(assets=[asset1, asset2])

    with DagsterInstance.ephemeral() as instance:
        asset_graph_view = AssetGraphView.for_test(
            defs, instance, effective_dt=create_datetime(2025, 2, 6)
        )

        # at midnight on 2025-02-06, 2025-02-06 exists on child asset but not on parent asset
        child_subset = asset_graph_view.get_asset_subset_from_asset_partitions(
            asset2.key,
            {
                AssetKeyPartitionKey(asset2.key, "2025-02-05"),
                AssetKeyPartitionKey(asset2.key, "2025-02-06"),
            },
        )

        parent_subset = asset_graph_view.compute_parent_subset(asset1.key, child_subset)

        assert parent_subset.expensively_compute_asset_partitions() == {
            AssetKeyPartitionKey(asset1.key, "2025-02-05"),
        }


def test_non_partitioned_depends_on_last_partition():
    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["a", "b", "c", "d"]))
    def upstream():
        pass

    @dg.asset(ins={"upstream": dg.AssetIn(partition_mapping=dg.LastPartitionMapping())})
    def downstream(upstream):
        assert upstream is None

    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            if context.asset_key == dg.AssetKey("upstream"):
                assert context.has_asset_partitions
                assert context.asset_partition_key == "b"
            else:
                assert not context.has_asset_partitions

        def load_input(self, context):
            assert context.has_asset_partitions
            assert context.asset_partition_key == "d"

    result = dg.materialize(
        assets=[upstream, downstream],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key="b",
    )
    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("upstream"),
        [dg.AssetMaterialization(dg.AssetKey(["upstream"]), partition="b")],
        exclude_fields=["tags"],
    )
    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("downstream"),
        [dg.AssetMaterialization(dg.AssetKey(["downstream"]))],
        exclude_fields=["tags"],
    )


def test_non_partitioned_depends_on_specific_partitions():
    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["a", "b", "c", "d"]))
    def upstream():
        pass

    @dg.asset(
        ins={
            "upstream": dg.AssetIn(
                partition_mapping=dg.SpecificPartitionsPartitionMapping(["a", "b"])
            )
        }
    )
    def downstream_a_b(upstream):
        assert upstream is None

    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            if context.asset_key == dg.AssetKey("upstream"):
                assert context.has_asset_partitions
                assert context.asset_partition_key == "b"
            else:
                assert not context.has_asset_partitions

        def load_input(self, context):
            assert context.has_asset_partitions
            assert set(context.asset_partition_keys) == {"a", "b"}

    result = dg.materialize(
        [upstream, downstream_a_b],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key="b",
    )
    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("upstream"),
        [dg.AssetMaterialization(dg.AssetKey(["upstream"]), partition="b")],
        exclude_fields=["tags"],
    )
    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("downstream_a_b"),
        [dg.AssetMaterialization(dg.AssetKey(["downstream_a_b"]))],
        exclude_fields=["tags"],
    )


def test_specific_partitions_partition_mapping_downstream_partitions():
    upstream_partitions_def = dg.StaticPartitionsDefinition(["a", "b", "c", "d"])
    downstream_partitions_def = dg.StaticPartitionsDefinition(["x", "y", "z"])
    partition_mapping = dg.SpecificPartitionsPartitionMapping(["a", "b"])

    # cases where at least one of the specific partitions is in the upstream partitions subset
    for partition_subset in [
        DefaultPartitionsSubset({"a"}),
        DefaultPartitionsSubset({"a", "b"}),
        DefaultPartitionsSubset({"a", "b", "c", "d"}),
    ]:
        assert (
            partition_mapping.get_downstream_partitions_for_partitions(
                partition_subset, upstream_partitions_def, downstream_partitions_def
            )
            == downstream_partitions_def.subset_with_all_partitions()
        )

    for partition_subset in [
        DefaultPartitionsSubset({"c"}),
        DefaultPartitionsSubset({"c", "d"}),
    ]:
        assert (
            partition_mapping.get_downstream_partitions_for_partitions(
                partition_subset, upstream_partitions_def, downstream_partitions_def
            )
            == downstream_partitions_def.empty_subset()
        )


def test_non_partitioned_depends_on_all_partitions():
    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["a", "b", "c", "d"]))
    def upstream():
        pass

    @dg.asset(ins={"upstream": dg.AssetIn(partition_mapping=dg.AllPartitionMapping())})
    def downstream(upstream):
        assert upstream is None

    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            if context.asset_key == dg.AssetKey("upstream"):
                assert context.has_asset_partitions
                assert context.asset_partition_key == "b"
            else:
                assert not context.has_asset_partitions

        def load_input(self, context):
            assert context.has_asset_partitions
            assert context.asset_partition_key_range == dg.PartitionKeyRange("a", "d")

    result = dg.materialize(
        assets=[upstream, downstream],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key="b",
    )
    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("upstream"),
        [dg.AssetMaterialization(dg.AssetKey(["upstream"]), partition="b")],
        exclude_fields=["tags"],
    )
    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("downstream"),
        [dg.AssetMaterialization(dg.AssetKey(["downstream"]))],
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

    @dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2022-09-11"))
    def upstream(context: AssetExecutionContext):
        assert context.partition_keys == ["2022-09-11"]

    @dg.asset(partitions_def=dg.WeeklyPartitionsDefinition(start_date="2022-09-11"))
    def downstream(context, upstream):
        assert (
            context.asset_partition_keys_for_input("upstream")
            == daily_partition_keys_for_week_2022_09_11
        )

    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            if context.asset_key == dg.AssetKey("upstream"):
                assert context.has_asset_partitions
                assert context.asset_partition_keys == ["2022-09-11"]

        def load_input(self, context):
            assert context.has_asset_partitions
            assert context.asset_partition_keys == daily_partition_keys_for_week_2022_09_11

    assert dg.materialize(
        assets=[upstream],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key="2022-09-11",
    ).success

    assert dg.materialize(
        assets=[downstream, upstream],
        selection=["upstream"],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key="2022-09-11",
    ).success


def test_timezone_error_partition_mapping():
    utc = dg.DailyPartitionsDefinition(start_date="2020-01-01")
    pacific = dg.DailyPartitionsDefinition(start_date="2020-01-01", timezone="US/Pacific")
    partition_mapping = dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=0)

    with pytest.raises(Exception, match="Timezones UTC and US/Pacific don't match"):
        partition_mapping.validate_partition_mapping(utc, pacific)

    @dg.asset(partitions_def=pacific)
    def upstream_asset():
        pass

    @dg.asset(deps=[upstream_asset], partitions_def=utc)
    def downstream_asset():
        pass

    @dg.asset(deps=[upstream_asset], partitions_def=pacific)
    def valid_downstream_asset():
        pass

    invalid_defs = dg.Definitions(assets=[upstream_asset, downstream_asset])

    with pytest.raises(
        Exception, match="Invalid partition mapping from downstream_asset to upstream_asset"
    ):
        invalid_defs.get_repository_def().validate_loadable()

    valid_defs = dg.Definitions(assets=[upstream_asset, valid_downstream_asset])
    valid_defs.get_repository_def().validate_loadable()

    # Specs that would otherwise be invalid are not checked in validate_loadable (since they
    # don't always have the needed partitions information for validation)
    invalid_upstream_asset_spec = dg.AssetSpec(key=upstream_asset.key, partitions_def=pacific)

    defs_with_invalid_asset_spec = dg.Definitions(
        assets=[invalid_upstream_asset_spec, downstream_asset]
    )

    defs_with_invalid_asset_spec.get_repository_def().validate_loadable()


def test_dependency_resolution_partition_mapping():
    @dg.asset(
        partitions_def=dg.DailyPartitionsDefinition(start_date="2020-01-01"),
        key_prefix=["staging"],
    )
    def upstream(context: AssetExecutionContext):
        partition_date_str = context.partition_key
        return partition_date_str

    @dg.asset(
        partitions_def=dg.DailyPartitionsDefinition(start_date="2020-01-01"),
        key_prefix=["staging"],
        ins={
            "upstream": dg.AssetIn(
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=0),
            )
        },
    )
    def downstream(context, upstream):
        context.log.info(upstream)
        return upstream

    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj): ...

        def load_input(self, context):
            assert context.asset_key.path == ["staging", "upstream"]
            assert context.partition_key == "2020-01-02"
            assert context.asset_partition_keys == ["2020-01-01", "2020-01-02"]

    dg.materialize(
        [upstream, downstream], resources={"io_manager": MyIOManager()}, partition_key="2020-01-02"
    )


def test_exported_partition_mappings_whitelisted():
    import dagster

    dagster_exports = (getattr(dagster, attr_name) for attr_name in dagster.__dir__())

    exported_partition_mapping_classes = {
        export
        for export in dagster_exports
        if inspect.isclass(export) and issubclass(export, dg.PartitionMapping)
    } - {dg.PartitionMapping}

    assert set(get_builtin_partition_mapping_types()) == exported_partition_mapping_classes


def test_multipartitions_def_partition_mapping_infer_identity():
    composite = dg.MultiPartitionsDefinition(
        {
            "abc": dg.StaticPartitionsDefinition(["a", "b", "c"]),
            "123": dg.StaticPartitionsDefinition(["1", "2", "3"]),
        }
    )

    @dg.asset(partitions_def=composite)
    def upstream(context):
        return 1

    @dg.asset(partitions_def=composite)
    def downstream(context: AssetExecutionContext, upstream):
        assert context.asset_partition_keys_for_input("upstream") == context.partition_keys
        return 1

    asset_graph = AssetGraph.from_assets([upstream, downstream])
    assets_job = dg.define_asset_job("foo", [upstream, downstream]).resolve(asset_graph=asset_graph)

    assert (
        asset_graph.get_partition_mapping(upstream.key, downstream.key)
        == dg.IdentityPartitionMapping()
    )
    assert assets_job.execute_in_process(
        partition_key=dg.MultiPartitionKey({"abc": "a", "123": "1"})
    ).success


def test_multipartitions_def_partition_mapping_infer_single_dim_to_multi():
    abc_def = dg.StaticPartitionsDefinition(["a", "b", "c"])

    composite = dg.MultiPartitionsDefinition(
        {
            "abc": abc_def,
            "123": dg.StaticPartitionsDefinition(["1", "2", "3"]),
        }
    )

    @dg.asset(partitions_def=abc_def)
    def upstream(context: AssetExecutionContext):
        assert context.partition_keys == ["a"]
        return 1

    @dg.asset(partitions_def=composite)
    def downstream(context: AssetExecutionContext, upstream):
        assert context.asset_partition_keys_for_input("upstream") == ["a"]
        assert context.partition_keys == [dg.MultiPartitionKey({"abc": "a", "123": "1"})]
        return 1

    asset_graph = AssetGraph.from_assets([upstream, downstream])

    assert (
        asset_graph.get_partition_mapping(upstream.key, downstream.key)
        == dg.MultiToSingleDimensionPartitionMapping()
    )

    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            if context.asset_key == dg.AssetKey("upstream"):
                assert context.has_asset_partitions
                assert context.asset_partition_keys == ["a"]

        def load_input(self, context):
            assert context.has_asset_partitions
            assert context.asset_partition_keys == ["a"]

    dg.materialize(
        [upstream],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key="a",
    )

    dg.materialize(
        [downstream, dg.SourceAsset(dg.AssetKey("upstream"), partitions_def=abc_def)],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key=dg.MultiPartitionKey({"abc": "a", "123": "1"}),
    )


def test_multipartitions_def_partition_mapping_infer_multi_to_single_dim():
    abc_def = dg.StaticPartitionsDefinition(["a", "b", "c"])

    composite = dg.MultiPartitionsDefinition(
        {
            "abc": abc_def,
            "123": dg.StaticPartitionsDefinition(["1", "2", "3"]),
        }
    )

    a_multipartition_keys = {
        dg.MultiPartitionKey(kv)
        for kv in [{"abc": "a", "123": "1"}, {"abc": "a", "123": "2"}, {"abc": "a", "123": "3"}]
    }

    @dg.asset(partitions_def=composite)
    def upstream(context):
        return 1

    @dg.asset(partitions_def=abc_def)
    def downstream(context: AssetExecutionContext, upstream):
        assert set(context.asset_partition_keys_for_input("upstream")) == a_multipartition_keys
        assert context.partition_keys == ["a"]
        return 1

    asset_graph = AssetGraph.from_assets([upstream, downstream])

    assert (
        asset_graph.get_partition_mapping(upstream.key, downstream.key)
        == dg.MultiToSingleDimensionPartitionMapping()
    )

    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert set(context.asset_partition_keys) == a_multipartition_keys

    for pk in a_multipartition_keys:
        dg.materialize(
            [upstream],
            resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
            partition_key=pk,
        )

    dg.materialize(
        [downstream, dg.SourceAsset(dg.AssetKey("upstream"), partitions_def=composite)],
        resources={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
        partition_key="a",
    )


def test_identity_partition_mapping():
    xy = dg.StaticPartitionsDefinition(["x", "y"])
    zx = dg.StaticPartitionsDefinition(["z", "x"])

    result = dg.IdentityPartitionMapping().get_upstream_mapped_partitions_result_for_partitions(
        zx.empty_subset().with_partition_keys(["z", "x"]), zx, xy
    )
    assert result.partitions_subset.get_partition_keys() == set(["x"])
    assert result.required_but_nonexistent_subset.get_partition_keys() == {"z"}
    assert result.required_but_nonexistent_partition_keys == ["z"]

    # Make sure repr() still can output the subset
    assert str(result.required_but_nonexistent_subset) == "DefaultPartitionsSubset(subset={'z'})"

    result = dg.IdentityPartitionMapping().get_downstream_partitions_for_partitions(
        zx.empty_subset().with_partition_keys(["z", "x"]), zx, xy
    )
    assert result.get_partition_keys() == set(["x"])


def test_partition_mapping_with_asset_deps():
    partitions_def = dg.DailyPartitionsDefinition(start_date="2023-08-15")

    ### With @asset and deps
    @dg.asset(partitions_def=partitions_def)
    def upstream():
        return

    @dg.asset(
        partitions_def=partitions_def,
        deps=[
            dg.AssetDep(
                upstream,
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
            )
        ],
    )
    def downstream(context: AssetExecutionContext):
        upstream_key = datetime.strptime(
            context.asset_partition_key_for_input("upstream"), "%Y-%m-%d"
        )

        current_partition_key = datetime.strptime(context.partition_key, "%Y-%m-%d")

        assert current_partition_key - upstream_key == timedelta(days=1)

    dg.materialize([upstream, downstream], partition_key="2023-08-20")

    assert downstream.get_partition_mapping(
        dg.AssetKey("upstream")
    ) == dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)

    ### With @multi_asset and AssetSpec
    asset_1 = dg.AssetSpec(key="asset_1")
    asset_2 = dg.AssetSpec(key="asset_2")

    asset_1_partition_mapping = dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
    asset_2_partition_mapping = dg.TimeWindowPartitionMapping(start_offset=-2, end_offset=-2)
    asset_3 = dg.AssetSpec(
        key="asset_3",
        deps=[
            dg.AssetDep(
                asset=asset_1,
                partition_mapping=asset_1_partition_mapping,
            ),
            dg.AssetDep(
                asset=asset_2,
                partition_mapping=asset_2_partition_mapping,
            ),
        ],
    )
    asset_4 = dg.AssetSpec(
        key="asset_4",
        deps=[
            dg.AssetDep(
                asset=asset_1,
                partition_mapping=asset_1_partition_mapping,
            ),
            dg.AssetDep(
                asset=asset_2,
                partition_mapping=asset_2_partition_mapping,
            ),
        ],
    )

    @dg.multi_asset(specs=[asset_1, asset_2], partitions_def=partitions_def)
    def multi_asset_1():
        return

    @dg.multi_asset(specs=[asset_3, asset_4], partitions_def=partitions_def)
    def multi_asset_2(context: AssetExecutionContext):
        asset_1_key = datetime.strptime(
            context.asset_partition_key_for_input("asset_1"), "%Y-%m-%d"
        )
        asset_2_key = datetime.strptime(
            context.asset_partition_key_for_input("asset_2"), "%Y-%m-%d"
        )

        current_partition_key = datetime.strptime(context.partition_key, "%Y-%m-%d")

        assert current_partition_key - asset_1_key == timedelta(days=1)
        assert current_partition_key - asset_2_key == timedelta(days=2)

        return

    dg.materialize([multi_asset_1, multi_asset_2], partition_key="2023-08-20")

    assert multi_asset_2.get_partition_mapping(dg.AssetKey("asset_1")) == asset_1_partition_mapping
    assert multi_asset_2.get_partition_mapping(dg.AssetKey("asset_2")) == asset_2_partition_mapping


def test_conflicting_mappings_with_asset_deps():
    partitions_def = dg.DailyPartitionsDefinition(start_date="2023-08-15")

    ### With @asset and deps
    @dg.asset(partitions_def=partitions_def)
    def upstream():
        return

    with pytest.raises(dg.DagsterInvariantViolationError, match="Cannot set a dependency on asset"):
        # full error msg: Cannot set a dependency on asset AssetKey(['upstream']) more than once per asset
        @dg.asset(
            partitions_def=partitions_def,
            deps=[
                dg.AssetDep(
                    upstream,
                    partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
                ),
                dg.AssetDep(
                    upstream,
                    partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-2, end_offset=-2),
                ),
            ],
        )
        def downstream():
            pass

    ### With @multi_asset and AssetSpec
    asset_1 = dg.AssetSpec(key="asset_1")
    asset_2 = dg.AssetSpec(key="asset_2")

    asset_1_partition_mapping = dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
    asset_2_partition_mapping = dg.TimeWindowPartitionMapping(start_offset=-2, end_offset=-2)
    asset_3 = dg.AssetSpec(
        key="asset_3",
        deps=[
            dg.AssetDep(
                asset=asset_1,
                partition_mapping=asset_1_partition_mapping,
            ),
            dg.AssetDep(
                asset=asset_2,
                partition_mapping=asset_2_partition_mapping,
            ),
        ],
    )
    asset_4 = dg.AssetSpec(
        key="asset_4",
        deps=[
            dg.AssetDep(
                asset=asset_1,
                partition_mapping=asset_1_partition_mapping,
            ),
            dg.AssetDep(
                asset=asset_2,
                # conflicting partition mapping to asset_3's dependency on asset_2
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-3, end_offset=-3),
            ),
        ],
    )

    with pytest.raises(
        dg.DagsterInvalidDefinitionError, match="Two different PartitionMappings for"
    ):
        # full error msg: Two different PartitionMappings for AssetKey(['asset_2']) provided for multi_asset multi_asset_2. Please use the same PartitionMapping for AssetKey(['asset_2']).
        @dg.multi_asset(
            specs=[asset_3, asset_4],
            partitions_def=partitions_def,
        )
        def multi_asset_2():
            pass


def test_self_dependent_partition_mapping_with_asset_deps():
    partitions_def = dg.DailyPartitionsDefinition(start_date="2023-08-15")

    ### With @asset and deps
    @dg.asset(
        partitions_def=partitions_def,
        deps=[
            dg.AssetDep(
                "self_dependent",
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
            )
        ],
    )
    def self_dependent(context: AssetExecutionContext):
        upstream_key = datetime.strptime(
            context.asset_partition_key_for_input("self_dependent"), "%Y-%m-%d"
        )

        current_partition_key = datetime.strptime(context.partition_key, "%Y-%m-%d")

        assert current_partition_key - upstream_key == timedelta(days=1)

    dg.materialize([self_dependent], partition_key="2023-08-20")

    assert self_dependent.get_partition_mapping(
        dg.AssetKey("self_dependent")
    ) == dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)

    ### With @multi_asset and AssetSpec
    asset_1 = dg.AssetSpec(
        key="asset_1",
        deps=[
            dg.AssetDep(
                asset="asset_1",
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
            ),
        ],
    )

    @dg.multi_asset(specs=[asset_1], partitions_def=partitions_def)
    def the_multi_asset(context: AssetExecutionContext):
        asset_1_key = datetime.strptime(
            context.asset_partition_key_for_input("asset_1"), "%Y-%m-%d"
        )

        current_partition_key = datetime.strptime(context.partition_key, "%Y-%m-%d")

        assert current_partition_key - asset_1_key == timedelta(days=1)

    dg.materialize([the_multi_asset], partition_key="2023-08-20")


def test_dynamic_partition_mapping_with_asset_deps():
    partitions_def = dg.DynamicPartitionsDefinition(name="fruits")

    ### With @asset and deps
    @dg.asset(partitions_def=partitions_def)
    def upstream():
        return

    @dg.asset(
        partitions_def=partitions_def,
        deps=[
            dg.AssetDep(
                upstream, partition_mapping=dg.SpecificPartitionsPartitionMapping(["apple"])
            )
        ],
    )
    def downstream(context: AssetExecutionContext):
        assert context.asset_partition_key_for_input("upstream") == "apple"
        assert context.partition_key == "orange"

    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions("fruits", ["apple"])
        dg.materialize([upstream], partition_key="apple", instance=instance)

        instance.add_dynamic_partitions("fruits", ["orange"])
        dg.materialize([upstream, downstream], partition_key="orange", instance=instance)

    ### With @multi_asset and AssetSpec
    asset_1 = dg.AssetSpec(
        key="asset_1",
    )
    asset_2 = dg.AssetSpec(
        key="asset_2",
        deps=[
            dg.AssetDep(
                asset=asset_1,
                partition_mapping=dg.SpecificPartitionsPartitionMapping(["apple"]),
            ),
        ],
    )

    @dg.multi_asset(specs=[asset_1], partitions_def=partitions_def)
    def asset_1_multi_asset():
        return

    @dg.multi_asset(specs=[asset_2], partitions_def=partitions_def)
    def asset_2_multi_asset(context: AssetExecutionContext):
        assert context.asset_partition_key_for_input("asset_1") == "apple"
        assert context.partition_key == "orange"

    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions("fruits", ["apple"])
        dg.materialize([asset_1_multi_asset], partition_key="apple", instance=instance)

        instance.add_dynamic_partitions("fruits", ["orange"])
        dg.materialize(
            [asset_1_multi_asset, asset_2_multi_asset], partition_key="orange", instance=instance
        )


def test_last_partition_mapping_get_downstream_partitions():
    upstream_partitions_def = dg.DailyPartitionsDefinition("2023-10-01")
    downstream_partitions_def = dg.DailyPartitionsDefinition("2023-10-01")

    current_time = datetime(2023, 10, 5, 1)

    assert dg.LastPartitionMapping().get_downstream_partitions_for_partitions(
        upstream_partitions_def.empty_subset().with_partition_keys(["2023-10-04"]),
        upstream_partitions_def,
        downstream_partitions_def,
        current_time,
    ) == downstream_partitions_def.empty_subset().with_partition_keys(
        downstream_partitions_def.get_partition_keys(current_time)
    )

    assert dg.LastPartitionMapping().get_downstream_partitions_for_partitions(
        upstream_partitions_def.empty_subset().with_partition_keys(["2023-10-03", "2023-10-04"]),
        upstream_partitions_def,
        downstream_partitions_def,
        current_time,
    ) == downstream_partitions_def.empty_subset().with_partition_keys(
        downstream_partitions_def.get_partition_keys(current_time)
    )

    assert (
        dg.LastPartitionMapping().get_downstream_partitions_for_partitions(
            upstream_partitions_def.empty_subset().with_partition_keys(["2023-10-03"]),
            upstream_partitions_def,
            downstream_partitions_def,
            current_time,
        )
        == downstream_partitions_def.empty_subset()
    )


def test_invalid_mappings_with_asset_deps():
    @dg.asset(
        partitions_def=dg.DailyPartitionsDefinition(start_date="2023-01-21"),
    )
    def daily_partitioned_asset():
        pass

    @dg.asset(
        ins={
            "daily_partitioned_asset": dg.AssetIn(
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
            )
        },
    )
    def unpartitioned_mapped_asset(daily_partitioned_asset):
        # this asset is not partitioned, so this mapping is invalid
        pass

    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["alpha", "beta"]))
    def static_mapped_asset(context: AssetExecutionContext, daily_partitioned_asset) -> None:
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Invalid partition mapping from unpartitioned_mapped_asset to daily_partitioned_asset",
    ):
        Definitions.validate_loadable(
            dg.Definitions(
                assets=[daily_partitioned_asset, unpartitioned_mapped_asset],
            )
        )

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Invalid partition mapping from static_mapped_asset to daily_partitioned_asset",
    ):
        Definitions.validate_loadable(
            dg.Definitions(
                assets=[daily_partitioned_asset, static_mapped_asset],
            )
        )


def test_time_window_partition_mapping_with_exclusions():
    """Test that TimeWindowPartitionMapping correctly handles excluded partitions with datetime exclusions."""
    excluded_partition_dts = [
        datetime(2023, 1, 7),  # Saturday
        datetime(2023, 1, 8),  # Sunday
        datetime(2023, 1, 14),  # Saturday
        datetime(2023, 1, 15),  # Sunday
    ]
    partitions_def_with_exclusions = dg.TimeWindowPartitionsDefinition(
        cron_schedule="@daily",
        start="2023-01-01",
        fmt="%Y-%m-%d",
        exclusions=excluded_partition_dts,
    )

    @dg.asset(partitions_def=partitions_def_with_exclusions)
    def upstream():
        return

    @dg.asset(
        partitions_def=partitions_def_with_exclusions,
        deps=[
            dg.AssetDep(
                upstream,
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
            )
        ],
    )
    def downstream(context: AssetExecutionContext):
        upstream_partition_dt = datetime.strptime(
            context.asset_partition_key_for_input("upstream"), "%Y-%m-%d"
        )
        current_partition_dt = datetime.strptime(context.partition_key, "%Y-%m-%d")
        assert upstream_partition_dt not in excluded_partition_dts
        assert current_partition_dt not in excluded_partition_dts
        assert current_partition_dt - upstream_partition_dt > timedelta(days=1)

    result = dg.materialize(assets=[upstream, downstream], partition_key="2023-01-09")

    assert_namedtuple_lists_equal(
        result.asset_materializations_for_node("downstream"),
        [dg.AssetMaterialization(dg.AssetKey(["downstream"]), partition="2023-01-09")],
        exclude_fields=["tags"],
    )
