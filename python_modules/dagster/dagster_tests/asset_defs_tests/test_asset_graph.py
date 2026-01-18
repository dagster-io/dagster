import time
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Optional, cast

import dagster as dg
import pytest
from dagster import AssetsDefinition, AutomationCondition
from dagster._core.definitions.assets.graph.asset_graph import AssetGraph
from dagster._core.definitions.assets.graph.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.assets.graph.base_asset_graph import (
    AssetCheckNode,
    BaseAssetGraph,
    BaseAssetNode,
)
from dagster._core.definitions.assets.graph.remote_asset_graph import (
    RemoteAssetGraph,
    RemoteWorkspaceAssetGraph,
)
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.partitions.mapping import UpstreamPartitionsResult
from dagster._core.definitions.partitions.subset import PartitionsSubset
from dagster._core.errors import DagsterDefinitionChangedDeserializationError
from dagster._core.instance import DynamicPartitionsStore
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._core.remote_representation.handle import RepositoryHandle
from dagster._core.test_utils import freeze_time, mock_workspace_from_repos
from dagster._time import create_datetime

if TYPE_CHECKING:
    from dagster._core.definitions.partitions.subset import TimeWindowPartitionsSubset


def to_remote_asset_graph(assets, asset_checks=None) -> RemoteAssetGraph:
    @dg.repository
    def repo():
        return assets + (asset_checks or [])

    remote_repo = RemoteRepository(
        RepositorySnap.from_def(repo),
        repository_handle=RepositoryHandle.for_test(location_name="fake", repository_name="repo"),
        auto_materialize_use_sensors=True,
    )
    return remote_repo.asset_graph


@pytest.fixture(
    name="asset_graph_from_assets", params=[AssetGraph.from_assets, to_remote_asset_graph]
)
def asset_graph_from_assets_fixture(
    request,
) -> Callable[[list[dg.AssetsDefinition]], BaseAssetGraph]:
    return request.param


def test_basics(asset_graph_from_assets):
    @dg.asset(code_version="1")
    def asset0(): ...

    @dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2022-01-01"))
    def asset1(asset0): ...

    @dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2022-01-01"))
    def asset2(asset0): ...

    @dg.asset(partitions_def=dg.HourlyPartitionsDefinition(start_date="2022-01-01-00:00"))
    def asset3(asset1, asset2): ...

    assets = [asset0, asset1, asset2, asset3]
    asset_graph = asset_graph_from_assets(assets)
    asset0_node = asset_graph.get(asset0.key)
    asset1_node = asset_graph.get(asset1.key)
    asset2_node = asset_graph.get(asset2.key)
    asset3_node = asset_graph.get(asset3.key)

    assert asset_graph.get_all_asset_keys() == {asset0.key, asset1.key, asset2.key, asset3.key}
    assert not asset0_node.is_partitioned
    assert asset1_node.is_partitioned
    assert asset1_node.partitions_def == asset2_node.partitions_def
    assert asset1_node.partitions_def != asset3_node.partitions_def
    assert asset0_node.child_keys == {asset1.key, asset2.key}
    assert asset3_node.parent_keys == {asset1.key, asset2.key}
    for node in [asset0_node, asset1_node, asset2_node, asset3_node]:
        assert node.execution_set_asset_keys == {node.key}
    assert asset0_node.code_version == "1"
    assert asset1_node.code_version is None


def test_get_children_partitions_unpartitioned_parent_partitioned_child(
    asset_graph_from_assets,
) -> None:
    @dg.asset
    def parent(): ...

    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["a", "b"]))
    def child(parent): ...

    asset_graph = asset_graph_from_assets([parent, child])

    expected_asset_partitions = {
        AssetKeyPartitionKey(child.key, "a"),
        AssetKeyPartitionKey(child.key, "b"),
    }
    assert asset_graph.get_children_partitions(parent.key) == expected_asset_partitions


def test_get_children_partitions_unpartitioned_parent_time_partitioned_child(
    asset_graph_from_assets,
) -> None:
    @dg.asset
    def parent(): ...

    @dg.asset(partitions_def=dg.DailyPartitionsDefinition("2023-01-01"))
    def child(parent): ...

    with partition_loading_context(effective_dt=create_datetime(2023, 1, 3, 0, 0, 0)):
        asset_graph = asset_graph_from_assets([parent, child])

        expected_asset_partitions = {
            AssetKeyPartitionKey(asset_key=dg.AssetKey(["child"]), partition_key="2023-01-01"),
            AssetKeyPartitionKey(asset_key=dg.AssetKey(["child"]), partition_key="2023-01-02"),
        }
        assert asset_graph.get_children_partitions(parent.key) == expected_asset_partitions


def test_get_parent_partitions_unpartitioned_child_partitioned_parent(
    asset_graph_from_assets: Callable[..., BaseAssetGraph],
):
    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["a", "b"]))
    def parent(): ...

    @dg.asset
    def child(parent): ...

    with (
        dg.instance_for_test() as instance,
        partition_loading_context(dynamic_partitions_store=instance),
    ):
        asset_graph = asset_graph_from_assets([parent, child])
        expected_asset_partitions = {
            AssetKeyPartitionKey(parent.key, "a"),
            AssetKeyPartitionKey(parent.key, "b"),
        }
        assert (
            asset_graph.get_parents_partitions(child.key).parent_partitions
            == expected_asset_partitions
        )


def test_get_children_partitions_fan_out(asset_graph_from_assets: Callable[..., BaseAssetGraph]):
    @dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2022-01-01"))
    def parent(): ...

    @dg.asset(partitions_def=dg.HourlyPartitionsDefinition(start_date="2022-01-01-00:00"))
    def child(parent): ...

    asset_graph = asset_graph_from_assets([parent, child])
    with (
        dg.instance_for_test() as instance,
        partition_loading_context(dynamic_partitions_store=instance),
    ):
        expected_asset_partitions = {
            AssetKeyPartitionKey(child.key, f"2022-01-03-{str(hour).zfill(2)}:00")
            for hour in range(24)
        }

        assert (
            asset_graph.get_children_partitions(parent.key, "2022-01-03")
            == expected_asset_partitions
        )


def test_get_parent_partitions_fan_in(
    asset_graph_from_assets: Callable[..., BaseAssetGraph],
) -> None:
    @dg.asset(partitions_def=dg.HourlyPartitionsDefinition(start_date="2022-01-01-00:00"))
    def parent(): ...

    @dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2022-01-01"))
    def child(parent): ...

    asset_graph = asset_graph_from_assets([parent, child])

    with (
        dg.instance_for_test() as instance,
        partition_loading_context(dynamic_partitions_store=instance),
    ):
        expected_asset_partitions = {
            AssetKeyPartitionKey(parent.key, f"2022-01-03-{str(hour).zfill(2)}:00")
            for hour in range(24)
        }
        child_asset_partition = AssetKeyPartitionKey(child.key, "2022-01-03")

        assert (
            asset_graph.get_parents_partitions(
                child.key, child_asset_partition.partition_key
            ).parent_partitions
            == expected_asset_partitions
        )


def test_get_parent_partitions_non_default_partition_mapping(
    asset_graph_from_assets: Callable[..., BaseAssetGraph],
):
    @dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2022-01-01"))
    def parent(): ...

    @dg.asset(ins={"parent": dg.AssetIn(partition_mapping=dg.LastPartitionMapping())})
    def child(parent): ...

    asset_graph = asset_graph_from_assets([parent, child])

    with freeze_time(create_datetime(year=2022, month=1, day=3, hour=4)):
        with (
            dg.instance_for_test() as instance,
            partition_loading_context(dynamic_partitions_store=instance),
        ):
            expected_asset_partitions = {AssetKeyPartitionKey(parent.key, "2022-01-02")}
            mapped_partitions_result = asset_graph.get_parents_partitions(child.key)
            assert mapped_partitions_result.parent_partitions == expected_asset_partitions
            assert mapped_partitions_result.required_but_nonexistent_parents_partitions == set()


def test_custom_unsupported_partition_mapping():
    class TrailingWindowPartitionMapping(dg.PartitionMapping):
        def get_upstream_mapped_partitions_result_for_partitions(
            self,
            downstream_partitions_subset: Optional[PartitionsSubset],
            downstream_partitions_def: Optional[dg.PartitionsDefinition],
            upstream_partitions_def: PartitionsDefinition,
            current_time: Optional[datetime] = None,
            dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
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
            downstream_partitions_def: Optional[dg.PartitionsDefinition],
        ):
            pass

        def get_downstream_partitions_for_partitions(
            self,
            upstream_partitions_subset: PartitionsSubset,
            upstream_partitions_def: PartitionsDefinition,
            downstream_partitions_def: PartitionsDefinition,
            current_time: Optional[datetime] = None,
            dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
        ) -> PartitionsSubset:
            raise NotImplementedError()

        @property
        def description(self) -> str:
            raise NotImplementedError()

    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["1", "2", "3"]))
    def parent(): ...

    with pytest.warns(
        DeprecationWarning,
        match=(
            "Non-built-in PartitionMappings, such as TrailingWindowPartitionMapping are deprecated"
            " and will not work with asset reconciliation. The built-in partition mappings are"
            " AllPartitionMapping, IdentityPartitionMapping"
        ),
    ):

        @dg.asset(
            partitions_def=dg.StaticPartitionsDefinition(["1", "2", "3"]),
            ins={"parent": dg.AssetIn(partition_mapping=TrailingWindowPartitionMapping())},
        )
        def child(parent): ...

    internal_asset_graph = AssetGraph.from_assets([parent, child])
    external_asset_graph = to_remote_asset_graph([parent, child])

    with (
        dg.instance_for_test() as instance,
        partition_loading_context(dynamic_partitions_store=instance),
    ):
        assert internal_asset_graph.get_parents_partitions(child.key, "2").parent_partitions == {
            AssetKeyPartitionKey(parent.key, "1"),
            AssetKeyPartitionKey(parent.key, "2"),
        }

        # external falls back to default PartitionMapping
        assert external_asset_graph.get_parents_partitions(child.key, "2").parent_partitions == {
            AssetKeyPartitionKey(parent.key, "2")
        }


def test_required_multi_asset_sets_non_subsettable_multi_asset(
    asset_graph_from_assets: Callable[..., BaseAssetGraph],
):
    @dg.multi_asset(outs={"a": dg.AssetOut(), "b": dg.AssetOut()})
    def non_subsettable_multi_asset(): ...

    asset_graph = asset_graph_from_assets([non_subsettable_multi_asset])
    for asset_key in non_subsettable_multi_asset.keys:
        assert (
            asset_graph.get(asset_key).execution_set_asset_keys == non_subsettable_multi_asset.keys
        )


def test_required_multi_asset_sets_subsettable_multi_asset(
    asset_graph_from_assets: Callable[..., BaseAssetGraph],
):
    @dg.multi_asset(
        outs={"a": dg.AssetOut(), "b": dg.AssetOut()},
        can_subset=True,
    )
    def subsettable_multi_asset(): ...

    asset_graph = asset_graph_from_assets([subsettable_multi_asset])
    for asset_key in subsettable_multi_asset.keys:
        assert asset_graph.get(asset_key).execution_set_asset_keys == {asset_key}


def test_required_multi_asset_sets_graph_backed_multi_asset(
    asset_graph_from_assets: Callable[..., BaseAssetGraph],
):
    @dg.op
    def op1():
        return 1

    @dg.op(out={"b": dg.Out(), "c": dg.Out()})
    def op2():
        return 4, 5

    @dg.graph(out={"a": dg.GraphOut(), "b": dg.GraphOut(), "c": dg.GraphOut()})
    def graph1():
        a = op1()
        b, c = op2()
        return a, b, c

    graph_backed_multi_asset = AssetsDefinition.from_graph(graph1)
    asset_graph = asset_graph_from_assets([graph_backed_multi_asset])
    for asset_key in graph_backed_multi_asset.keys:
        assert asset_graph.get(asset_key).execution_set_asset_keys == graph_backed_multi_asset.keys


def test_required_multi_asset_sets_same_op_in_different_assets(
    asset_graph_from_assets: Callable[..., BaseAssetGraph],
):
    @dg.op
    def op1(): ...

    asset1 = AssetsDefinition.from_op(op1, keys_by_output_name={"result": dg.AssetKey("a")})
    asset2 = AssetsDefinition.from_op(op1, keys_by_output_name={"result": dg.AssetKey("b")})
    assets = [asset1, asset2]

    asset_graph = asset_graph_from_assets(assets)
    for asset_def in assets:
        assert asset_graph.get(asset_def.key).execution_set_asset_keys == {asset_def.key}


def test_partitioned_source_asset(asset_graph_from_assets: Callable[..., BaseAssetGraph]):
    partitions_def = dg.DailyPartitionsDefinition(start_date="2022-01-01")

    partitioned_source = dg.SourceAsset(
        "partitioned_source",
        partitions_def=partitions_def,
    )

    @dg.asset(partitions_def=partitions_def, deps=["partitioned_source"])
    def downstream_of_partitioned_source():
        pass

    asset_graph = asset_graph_from_assets([partitioned_source, downstream_of_partitioned_source])

    if isinstance(asset_graph, RemoteAssetGraph):
        pytest.xfail("not supported with RemoteAssetGraph")

    assert asset_graph.get(dg.AssetKey("partitioned_source")).is_partitioned
    assert asset_graph.get(dg.AssetKey("downstream_of_partitioned_source")).is_partitioned


def test_bfs_filter_asset_subsets(asset_graph_from_assets: Callable[..., BaseAssetGraph]):
    daily_partitions_def = dg.DailyPartitionsDefinition(start_date="2022-01-01")

    @dg.asset(partitions_def=daily_partitions_def)
    def asset0(): ...

    @dg.asset(partitions_def=daily_partitions_def)
    def asset1(asset0): ...

    @dg.asset(partitions_def=daily_partitions_def)
    def asset2(asset0): ...

    @dg.asset(partitions_def=dg.HourlyPartitionsDefinition(start_date="2022-01-01-00:00"))
    def asset3(asset1, asset2): ...

    asset_graph = asset_graph_from_assets([asset0, asset1, asset2, asset3])

    def include_all(asset_key, partitions_subset):
        return True

    initial_partitions_subset = daily_partitions_def.empty_subset().with_partition_keys(
        ["2022-01-02", "2022-01-03"]
    )
    initial_asset1_subset = AssetGraphSubset(
        partitions_subsets_by_asset_key={asset1.key: initial_partitions_subset}
    )
    assert asset3.partitions_def is not None
    corresponding_asset3_subset = AssetGraphSubset(
        partitions_subsets_by_asset_key={
            asset3.key: asset3.partitions_def.empty_subset().with_partition_key_range(
                asset3.partitions_def,
                dg.PartitionKeyRange("2022-01-02-00:00", "2022-01-03-23:00"),
            ),
        },
    )

    assert (
        asset_graph.bfs_filter_subsets(
            initial_subset=initial_asset1_subset,
            condition_fn=include_all,
        )
        == initial_asset1_subset | corresponding_asset3_subset
    )

    def include_none(asset_key, partitions_subset):
        return False

    assert (
        asset_graph.bfs_filter_subsets(
            initial_subset=initial_asset1_subset, condition_fn=include_none
        )
        == AssetGraphSubset()
    )

    def exclude_asset3(asset_key, partitions_subset):
        return asset_key is not asset3.key

    assert (
        asset_graph.bfs_filter_subsets(
            initial_subset=initial_asset1_subset, condition_fn=exclude_asset3
        )
        == initial_asset1_subset
    )

    def exclude_asset2(asset_key, partitions_subset):
        return asset_key is not asset2.key

    initial_asset0_subset = AssetGraphSubset(
        partitions_subsets_by_asset_key={asset0.key: initial_partitions_subset}
    )
    assert (
        asset_graph.bfs_filter_subsets(
            initial_subset=initial_asset0_subset, condition_fn=exclude_asset2
        )
        == initial_asset0_subset | initial_asset1_subset | corresponding_asset3_subset
    )


def test_subset_from_asset_partitions(
    asset_graph_from_assets: Callable[..., BaseAssetGraph],
):
    daily_partitions_def = dg.DailyPartitionsDefinition(start_date="2022-01-01")

    @dg.asset(partitions_def=daily_partitions_def)
    def asset0(): ...

    keys = {
        AssetKeyPartitionKey(asset0.key, "2021-12-31"),
        AssetKeyPartitionKey(asset0.key, "2022-01-01"),
        AssetKeyPartitionKey(asset0.key, "2022-02-02"),
    }

    subset = AssetGraphSubset.from_asset_partition_set(keys, asset_graph_from_assets([asset0]))

    assert subset == AssetGraphSubset(
        partitions_subsets_by_asset_key={
            asset0.key: daily_partitions_def.subset_with_partition_keys(
                ["2022-01-01", "2022-02-02"]
            )
        },
    )

    subset_without_validation = AssetGraphSubset.from_asset_partition_set(
        keys, asset_graph_from_assets([asset0]), validate_time_range=False
    )

    assert subset_without_validation == AssetGraphSubset(
        partitions_subsets_by_asset_key={
            asset0.key: cast(
                "TimeWindowPartitionsSubset", daily_partitions_def.empty_subset()
            ).with_partition_keys(["2021-12-31", "2022-01-01", "2022-02-02"], validate=False)
        },
    )


def test_bfs_filter_asset_subsets_different_mappings(
    asset_graph_from_assets: Callable[..., BaseAssetGraph],
):
    daily_partitions_def = dg.DailyPartitionsDefinition(start_date="2022-01-01")

    @dg.asset(partitions_def=daily_partitions_def)
    def asset0(): ...

    @dg.asset(partitions_def=daily_partitions_def)
    def asset1(asset0): ...

    @dg.asset(
        partitions_def=daily_partitions_def,
        ins={
            "asset0": dg.AssetIn(
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
            )
        },
    )
    def asset2(asset0): ...

    @dg.asset(partitions_def=daily_partitions_def)
    def asset3(asset1, asset2): ...

    asset_graph = asset_graph_from_assets([asset0, asset1, asset2, asset3])

    def include_all(asset_key, partitions_subset):
        return True

    initial_subset = daily_partitions_def.subset_with_partition_keys(["2022-01-01"])
    expected_asset2_partitions_subset = daily_partitions_def.subset_with_partition_keys(
        ["2022-01-02"]
    )
    expected_asset3_partitions_subset = daily_partitions_def.subset_with_partition_keys(
        ["2022-01-01", "2022-01-02"]
    )
    expected_asset_graph_subset = AssetGraphSubset(
        partitions_subsets_by_asset_key={
            asset0.key: initial_subset,
            asset1.key: initial_subset,
            asset2.key: expected_asset2_partitions_subset,
            asset3.key: expected_asset3_partitions_subset,
        },
    )

    assert (
        asset_graph.bfs_filter_subsets(
            initial_subset=AssetGraphSubset(
                partitions_subsets_by_asset_key={asset0.key: initial_subset},
            ),
            condition_fn=include_all,
        )
        == expected_asset_graph_subset
    )


def test_asset_graph_subset_contains(
    asset_graph_from_assets: Callable[..., BaseAssetGraph],
) -> None:
    daily_partitions_def = dg.DailyPartitionsDefinition(start_date="2022-01-01")

    @dg.asset(partitions_def=daily_partitions_def)
    def partitioned1(): ...

    @dg.asset(partitions_def=daily_partitions_def)
    def partitioned2(): ...

    @dg.asset
    def unpartitioned1(): ...

    @dg.asset
    def unpartitioned2(): ...

    asset_graph_subset = AssetGraphSubset(
        partitions_subsets_by_asset_key={
            partitioned1.key: daily_partitions_def.subset_with_partition_keys(["2022-01-01"]),
            partitioned2.key: daily_partitions_def.empty_subset(),
        },
        non_partitioned_asset_keys={unpartitioned1.key},
    )

    assert unpartitioned1.key in asset_graph_subset
    assert AssetKeyPartitionKey(unpartitioned1.key) in asset_graph_subset
    assert partitioned1.key in asset_graph_subset
    assert AssetKeyPartitionKey(partitioned1.key, "2022-01-01") in asset_graph_subset
    assert AssetKeyPartitionKey(partitioned1.key, "2022-01-02") not in asset_graph_subset
    assert unpartitioned2.key not in asset_graph_subset
    assert AssetKeyPartitionKey(unpartitioned2.key) not in asset_graph_subset
    assert partitioned2.key not in asset_graph_subset
    assert AssetKeyPartitionKey(partitioned2.key, "2022-01-01") not in asset_graph_subset


def test_asset_graph_difference(asset_graph_from_assets: Callable[..., BaseAssetGraph]):
    daily_partitions_def = dg.DailyPartitionsDefinition(start_date="2022-01-01")

    @dg.asset(partitions_def=daily_partitions_def)
    def partitioned1(): ...

    @dg.asset(partitions_def=daily_partitions_def)
    def partitioned2(): ...

    @dg.asset
    def unpartitioned1(): ...

    @dg.asset
    def unpartitioned2(): ...

    subset1 = AssetGraphSubset(
        partitions_subsets_by_asset_key={
            partitioned1.key: daily_partitions_def.subset_with_partition_keys(
                ["2022-01-01", "2022-01-02", "2022-01-03"]
            ),
            partitioned2.key: daily_partitions_def.subset_with_partition_keys(
                ["2022-01-01", "2022-01-02"]
            ),
        },
        non_partitioned_asset_keys={unpartitioned1.key},
    )

    subset2 = AssetGraphSubset(
        partitions_subsets_by_asset_key={
            partitioned1.key: daily_partitions_def.subset_with_partition_keys(
                ["2022-01-02", "2022-01-03", "2022-01-04"]
            ),
            partitioned2.key: daily_partitions_def.subset_with_partition_keys(
                ["2022-01-01", "2022-01-02", "2022-01-03", "2022-01-04"]
            ),
        },
        non_partitioned_asset_keys={unpartitioned1.key, unpartitioned2.key},
    )

    assert len(list((subset1 - subset1).iterate_asset_partitions())) == 0
    assert len(list((subset2 - subset2).iterate_asset_partitions())) == 0
    assert subset1 - subset2 == AssetGraphSubset(
        partitions_subsets_by_asset_key={
            partitioned1.key: daily_partitions_def.subset_with_partition_keys(["2022-01-01"]),
            partitioned2.key: daily_partitions_def.empty_subset(),
        },
        non_partitioned_asset_keys=set(),
    )
    assert subset2 - subset1 == AssetGraphSubset(
        partitions_subsets_by_asset_key={
            partitioned1.key: daily_partitions_def.subset_with_partition_keys(["2022-01-04"]),
            partitioned2.key: daily_partitions_def.subset_with_partition_keys(
                ["2022-01-03", "2022-01-04"]
            ),
        },
        non_partitioned_asset_keys={unpartitioned2.key},
    )


def test_asset_graph_partial_deserialization(
    asset_graph_from_assets: Callable[..., BaseAssetGraph],
):
    daily_partitions_def = dg.DailyPartitionsDefinition(start_date="2022-01-01")
    static_partitions_def = dg.StaticPartitionsDefinition(["a", "b", "c"])

    def get_ag1() -> BaseAssetGraph:
        @dg.asset(partitions_def=daily_partitions_def)
        def partitioned1(): ...

        @dg.asset(partitions_def=daily_partitions_def)
        def partitioned2(): ...

        @dg.asset
        def unpartitioned1(): ...

        @dg.asset
        def unpartitioned2(): ...

        return asset_graph_from_assets([partitioned1, partitioned2, unpartitioned1, unpartitioned2])

    def get_ag2() -> BaseAssetGraph:
        @dg.asset(partitions_def=daily_partitions_def)
        def partitioned1(): ...

        # new partitions_def
        @dg.asset(partitions_def=static_partitions_def)
        def partitioned2(): ...

        # new asset
        @dg.asset(partitions_def=static_partitions_def)
        def partitioned3(): ...

        @dg.asset
        def unpartitioned2(): ...

        @dg.asset
        def unpartitioned3(): ...

        return asset_graph_from_assets(
            [partitioned1, partitioned2, partitioned3, unpartitioned2, unpartitioned3]
        )

    ag1_storage_dict = AssetGraphSubset(
        partitions_subsets_by_asset_key={
            dg.AssetKey("partitioned1"): daily_partitions_def.subset_with_partition_keys(
                ["2022-01-01", "2022-01-02", "2022-01-03"]
            ),
            dg.AssetKey("partitioned2"): daily_partitions_def.subset_with_partition_keys(
                ["2022-01-01", "2022-01-02", "2022-01-03"]
            ),
        },
        non_partitioned_asset_keys={
            dg.AssetKey("unpartitioned1"),
            dg.AssetKey("unpartitioned2"),
        },
    ).to_storage_dict(asset_graph=get_ag1())

    asset_graph2 = get_ag2()
    assert not AssetGraphSubset.can_deserialize(ag1_storage_dict, asset_graph2)
    with pytest.raises(DagsterDefinitionChangedDeserializationError):
        AssetGraphSubset.from_storage_dict(
            ag1_storage_dict,
            asset_graph=asset_graph2,
        )

    ag2_subset = AssetGraphSubset.from_storage_dict(
        ag1_storage_dict, asset_graph=asset_graph2, allow_partial=True
    )
    assert ag2_subset == AssetGraphSubset(
        partitions_subsets_by_asset_key={
            dg.AssetKey("partitioned1"): daily_partitions_def.subset_with_partition_keys(
                ["2022-01-01", "2022-01-02", "2022-01-03"]
            )
        },
        non_partitioned_asset_keys={dg.AssetKey("unpartitioned2")},
    )


def test_required_assets_and_checks_by_key_check_decorator(
    asset_graph_from_assets: Callable[..., BaseAssetGraph[BaseAssetNode]],
) -> None:
    @dg.asset
    def asset0(): ...

    @dg.asset_check(asset=asset0)  # pyright: ignore[reportArgumentType]
    def check0(): ...

    @dg.asset_check(  # pyright: ignore[reportArgumentType]
        asset=asset0,
        blocking=True,
        automation_condition=AutomationCondition.cron_tick_passed("*/15 * * * *"),
    )
    def check1(): ...

    asset_graph = asset_graph_from_assets([asset0, check0, check1])
    assert asset_graph.get_execution_set_asset_and_check_keys(asset0.key) == {asset0.key}
    assert asset_graph.get_execution_set_asset_and_check_keys(next(iter(check0.check_keys))) == {
        dg.AssetCheckKey(asset0.key, "check0")
    }
    assert asset_graph.get_execution_set_asset_and_check_keys(next(iter(check1.check_keys))) == {
        dg.AssetCheckKey(asset0.key, "check1")
    }

    check_node = asset_graph.get(check0.check_key)
    assert isinstance(check_node, AssetCheckNode)
    assert check_node.key == check0.check_key
    assert not check_node.blocking
    assert check_node.partitions_def is None

    check_node = asset_graph.get(check1.check_key)
    assert check_node.blocking
    assert check_node.partitions_def is None
    assert check_node.automation_condition == AutomationCondition.cron_tick_passed("*/15 * * * *")


def test_toposort(
    asset_graph_from_assets: Callable[..., BaseAssetGraph],
) -> None:
    @dg.asset
    def A(): ...

    @dg.asset(deps=[A])
    def B(): ...

    @dg.asset_check(asset=A)  # pyright: ignore[reportArgumentType]
    def Ac(): ...

    @dg.asset_check(asset=B)  # pyright: ignore[reportArgumentType]
    def Bc(): ...

    asset_graph = asset_graph_from_assets([A, B, Ac, Bc])

    assert asset_graph.toposorted_asset_keys == [A.key, B.key]
    assert asset_graph.toposorted_entity_keys_by_level == [
        [A.key],
        [Ac.check_key, B.key],
        [Bc.check_key],
    ]


def test_required_assets_and_checks_by_key_asset_decorator(
    asset_graph_from_assets: Callable[..., BaseAssetGraph],
):
    foo_check = dg.AssetCheckSpec(name="foo", asset="asset0")
    bar_check = dg.AssetCheckSpec(name="bar", asset="asset0")

    @dg.asset(check_specs=[foo_check, bar_check])
    def asset0(): ...

    @dg.asset_check(asset=asset0)  # pyright: ignore[reportArgumentType]
    def check0(): ...

    asset_graph = asset_graph_from_assets([asset0, check0])

    grouped_keys = [asset0.key, foo_check.key, bar_check.key]
    for key in grouped_keys:
        assert asset_graph.get_execution_set_asset_and_check_keys(key) == set(grouped_keys)

    assert asset_graph.get_execution_set_asset_and_check_keys(next(iter(check0.check_keys))) == {
        dg.AssetCheckKey(asset0.key, "check0")
    }


def test_required_assets_and_checks_by_key_multi_asset(
    asset_graph_from_assets: Callable[..., BaseAssetGraph],
):
    foo_check = dg.AssetCheckSpec(name="foo", asset="asset0")
    bar_check = dg.AssetCheckSpec(name="bar", asset="asset1")

    @dg.multi_asset(
        outs={"asset0": dg.AssetOut(), "asset1": dg.AssetOut()},
        check_specs=[foo_check, bar_check],
    )
    def asset_fn(): ...

    biz_check = dg.AssetCheckSpec(name="bar", asset="subsettable_asset0")

    @dg.multi_asset(
        outs={"subsettable_asset0": dg.AssetOut(), "subsettable_asset1": dg.AssetOut()},
        check_specs=[biz_check],
        can_subset=True,
    )
    def subsettable_asset_fn(): ...

    asset_graph = asset_graph_from_assets([asset_fn, subsettable_asset_fn])

    grouped_keys = [
        dg.AssetKey(["asset0"]),
        dg.AssetKey(["asset1"]),
        foo_check.key,
        bar_check.key,
    ]
    for key in grouped_keys:
        assert asset_graph.get_execution_set_asset_and_check_keys(key) == set(grouped_keys)

    for key in [
        dg.AssetKey(["subsettable_asset0"]),
        dg.AssetKey(["subsettable_asset1"]),
        biz_check.key,
    ]:
        assert asset_graph.get_execution_set_asset_and_check_keys(key) == {key}


def test_required_assets_and_checks_by_key_multi_asset_single_asset(
    asset_graph_from_assets: Callable[..., BaseAssetGraph],
):
    foo_check = dg.AssetCheckSpec(name="foo", asset="asset0")
    bar_check = dg.AssetCheckSpec(name="bar", asset="asset0")

    @dg.multi_asset(
        outs={"asset0": dg.AssetOut()},
        check_specs=[foo_check, bar_check],
        can_subset=True,
    )
    def asset_fn(): ...

    asset_graph = asset_graph_from_assets([asset_fn])

    for key in [dg.AssetKey(["asset0"]), foo_check.key, bar_check.key]:
        assert asset_graph.get_execution_set_asset_and_check_keys(key) == {key}


def test_multi_asset_check(
    asset_graph_from_assets: Callable[..., BaseAssetGraph],
):
    @dg.asset
    def asset0(): ...

    foo_check = dg.AssetCheckSpec(name="foo", asset="asset0")
    bar_check = dg.AssetCheckSpec(name="bar", asset="asset0")

    @dg.multi_asset_check(
        specs=[foo_check, bar_check],
    )
    def multi_check_1(): ...

    biz_check = dg.AssetCheckSpec(name="biz", asset="asset0")
    buz_check = dg.AssetCheckSpec(name="buz", asset="asset0")

    @dg.multi_asset_check(
        specs=[biz_check, buz_check],
        can_subset=True,
    )
    def multi_check_2(): ...

    asset_graph = asset_graph_from_assets([asset0, multi_check_1, multi_check_2])

    for key in [foo_check.key, bar_check.key]:
        assert asset_graph.get_execution_set_asset_and_check_keys(key) == {
            foo_check.key,
            bar_check.key,
        }

    for key in [biz_check.key, buz_check.key]:
        assert asset_graph.get_execution_set_asset_and_check_keys(key) == {key}


def test_multi_asset_with_many_specs():
    @dg.multi_asset(
        name="metabase_questions",
        compute_kind="metabase",
        specs=[
            dg.AssetSpec(
                key=["metabase", str(i)],
                metadata={"id": str(i)},
            )
            for i in range(6000)
        ],
        can_subset=True,
    )
    def my_multi_asset_with_many_specs():
        pass

    defs = dg.Definitions(assets=[my_multi_asset_with_many_specs])

    start_time = time.time()
    defs.resolve_all_job_defs()

    end_time = time.time()

    assert end_time - start_time < 15, "multi asset took too long to load"


def test_check_deps(asset_graph_from_assets: Callable[..., BaseAssetGraph]) -> None:
    @dg.asset
    def A() -> None: ...

    one = dg.AssetCheckSpec(name="one", asset="A", additional_deps=["B", "C"])
    two = dg.AssetCheckSpec(name="two", asset="B", additional_deps=["C", "D"])
    three = dg.AssetCheckSpec(name="three", asset="B")

    @dg.multi_asset_check(specs=[one, two, three])
    def multi_check(): ...

    asset_graph = asset_graph_from_assets([A, multi_check])

    assert asset_graph.get(one.key).parent_entity_keys == {
        dg.AssetKey("A"),
        dg.AssetKey("B"),
        dg.AssetKey("C"),
    }
    assert asset_graph.get(two.key).parent_entity_keys == {
        dg.AssetKey("B"),
        dg.AssetKey("C"),
        dg.AssetKey("D"),
    }
    assert asset_graph.get(three.key).parent_entity_keys == {dg.AssetKey("B")}


def test_cross_code_location_partition_mapping() -> None:
    @dg.asset(partitions_def=dg.HourlyPartitionsDefinition(start_date="2022-01-01-00:00"))
    def a(): ...

    @dg.repository
    def repo_a():
        return [a]

    @dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2022-01-01"), deps=["a"])
    def b(): ...

    @dg.repository
    def repo_b():
        return [b]

    asset_graph = mock_workspace_from_repos([repo_a, repo_b]).asset_graph

    assert isinstance(
        asset_graph.get_partition_mapping(key=b.key, parent_asset_key=a.key),
        dg.TimeWindowPartitionMapping,
    )


def test_serdes() -> None:
    @dg.asset
    def a(): ...

    @dg.asset_check(asset=a)  # pyright: ignore[reportArgumentType]
    def c(): ...

    @dg.repository
    def repo():
        return [a, c]

    asset_graph = mock_workspace_from_repos([repo]).asset_graph
    for node in asset_graph.asset_nodes:
        assert node == dg.deserialize_value(dg.serialize_value(node))

    check = next(iter(asset_graph.get_checks_for_asset(dg.AssetKey("a"))))
    assert check == dg.deserialize_value(dg.serialize_value(check))


def test_get_assets_for_same_storage_address() -> None:
    @dg.asset(metadata={"dagster/table_name": "db.schema.table_a"})
    def asset1(): ...

    @dg.asset(
        metadata={"dagster/table_name": "DB.SCHEMA.TABLE_A"}
    )  # uppercase, should match asset1
    def asset2(): ...

    @dg.asset(metadata={"dagster/table_name": "db.schema.table_b"})
    def asset3(): ...

    @dg.asset  # no table_name metadata
    def asset4(): ...

    assets = [asset1, asset2, asset3, asset4]

    @dg.repository
    def repo():
        return assets

    workspace = mock_workspace_from_repos([repo])
    asset_graph = workspace.asset_graph
    assert isinstance(asset_graph, RemoteWorkspaceAssetGraph)

    # Test: asset1 should find asset2 (same table, case-insensitive), not itself or others
    result = asset_graph.get_assets_for_same_storage_address(asset1.key)
    assert result == {asset_graph.get(asset2.key)}

    # Test: asset2 (uppercase) should find asset1 (lowercase)
    result = asset_graph.get_assets_for_same_storage_address(asset2.key)
    assert result == {asset_graph.get(asset1.key)}

    # Test: asset3 has unique table, should return empty
    result = asset_graph.get_assets_for_same_storage_address(asset3.key)
    assert result == set()

    # Test: asset4 has no table_name, should return empty
    result = asset_graph.get_assets_for_same_storage_address(asset4.key)
    assert result == set()

    # Test: non-existent key should return empty
    result = asset_graph.get_assets_for_same_storage_address(dg.AssetKey("nonexistent"))
    assert result == set()
