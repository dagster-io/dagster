from typing import TYPE_CHECKING, AbstractSet, Iterable, Mapping, NamedTuple, Optional, Set

import dagster._check as check
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_graph_computation import AssetGraphComputation

from ..errors import DagsterInvariantViolationError
from .asset_key import AssetKey, AssetKeyOrCheckKey
from .dependency import NodeHandle, NodeInputHandle, NodeOutputHandle

if TYPE_CHECKING:
    from dagster._core.definitions.asset_graph import AssetGraph, AssetNode
    from dagster._core.definitions.assets import AssetsDefinition
    from dagster._core.definitions.partition_mapping import PartitionMapping


class AssetLayer(NamedTuple):
    """Stores all of the asset-related information for a Dagster job. Maps each
    input / output in the underlying graph to the asset it represents (if any), and records the
    dependencies between each asset.
    """

    asset_graph: "AssetGraph"
    computation: AssetGraphComputation
    original_assets_defs_by_op_handle: Mapping[NodeHandle, "AssetsDefinition"]

    @property
    def all_asset_keys(self) -> Iterable[AssetKey]:
        return self.asset_graph.all_asset_keys

    @property
    def executable_asset_keys(self) -> Iterable[AssetKey]:
        return self.asset_graph.executable_asset_keys

    def get(self, asset_key: AssetKey) -> "AssetNode":
        return self.asset_graph.get(asset_key)

    def has(self, asset_key: AssetKey) -> bool:
        return self.asset_graph.has(asset_key)

    def node_output_handle_for_asset(self, asset_key: AssetKey) -> NodeOutputHandle:
        matching_handles = [
            handle
            for handle, handle_asset_key in self.computation.asset_or_check_keys_by_op_output_handle.items()
            if handle_asset_key == asset_key
        ]
        check.invariant(len(matching_handles) == 1)
        return matching_handles[0]

    def assets_def_for_node(self, node_handle: NodeHandle) -> Optional["AssetsDefinition"]:
        return self.original_assets_defs_by_op_handle.get(node_handle)

    def asset_keys_for_node(self, node_handle: NodeHandle) -> AbstractSet[AssetKey]:
        # assets_def = self.assets_def_for_node(node_handle)
        # return check.not_none(assets_def).keys
        return self.computation.asset_or_check_keys_by_op_handle[node_handle]

    def asset_key_for_node(self, node_handle: NodeHandle) -> AssetKey:
        asset_keys = self.asset_keys_for_node(node_handle)
        if len(asset_keys) > 1:
            raise DagsterInvariantViolationError(
                "Cannot call `asset_key_for_node` in a multi_asset with more than one asset."
                " Multiple asset keys defined."
            )
        return next(iter(asset_keys))

    def get_output_name_for_asset_check(self, asset_check_key: AssetCheckKey) -> str:
        """Output name in the leaf op."""
        return self.computation.op_output_handles_by_asset_or_check_key[asset_check_key].output_name

    def asset_key_for_input(self, node_handle: NodeHandle, input_name: str) -> Optional[AssetKey]:
        return self.computation.asset_keys_by_node_input_handle.get(
            NodeInputHandle(node_handle=node_handle, input_name=input_name)
        )

    def input_for_asset_key(self, node_handle: NodeHandle, key: AssetKey) -> Optional[str]:
        return next(
            (
                input_handle.input_name
                for input_handle, k in self.computation.asset_keys_by_node_input_handle.items()
                if k == key
            ),
            None,
        )

    def asset_key_for_output(self, node_handle: NodeHandle, output_name: str) -> Optional[AssetKey]:
        asset_or_check_key = self.computation.asset_or_check_keys_by_op_output_handle.get(
            NodeOutputHandle(node_handle=node_handle, output_name=output_name)
        )
        return asset_or_check_key if isinstance(asset_or_check_key, AssetKey) else None

    def asset_check_key_for_output(
        self, node_handle: NodeHandle, output_name: str
    ) -> Optional[AssetCheckKey]:
        asset_or_check_key = self.computation.asset_or_check_keys_by_op_output_handle.get(
            NodeOutputHandle(node_handle=node_handle, output_name=output_name)
        )
        return asset_or_check_key if isinstance(asset_or_check_key, AssetCheckKey) else None

    def partition_mapping_for_node_input(
        self, node_handle: NodeHandle, upstream_asset_key: AssetKey
    ) -> Optional["PartitionMapping"]:
        assets_def = self.assets_def_for_node(node_handle)
        if assets_def is not None:
            return assets_def.get_partition_mapping_for_dep(upstream_asset_key)
        else:
            # Can end up here when a non-asset job has an asset as an input
            return None

    def downstream_dep_assets_and_checks(
        self, node_handle: NodeHandle, output_name: str
    ) -> Set[AssetKeyOrCheckKey]:
        """Given the node handle of an op within a graph-backed asset and an output name,
        returns the asset keys dependent on that output.

        For example, for the following asset:

        @op(out={"out_1": Out(is_required=False), "out_2": Out(is_required=False)})
        def two_outputs_op(context):
            return 1, 1


        @op
        def add_one(x):
            return x + 1


        @graph(out={"asset_one": GraphOut(), "asset_two": GraphOut()})
        def my_graph():
            out_1, out_2 = two_outputs_op()
            return {"asset_one": out_1, "asset_two": add_one(out_2)}

        two_assets = AssetsDefinition.from_graph(my_graph)

        Calling downstream_dep_assets with the node handle of two_outputs_op will return:
        - {AssetKey("asset_one")} if output_name="out_1"
        - {AssetKey("asset_two")} if output_name="out_2"

        Calling downstream_dep_assets with node handle add_one will return:
        - {AssetKey("asset_two")} if output_name="result"
        """
        return {
            key
            for key in self.computation.asset_or_check_keys_by_dep_op_output_handle[
                NodeOutputHandle(node_handle=node_handle, output_name=output_name)
            ]
        }

    def upstream_dep_op_handles(self, asset_key: AssetKey) -> AbstractSet[NodeHandle]:
        return self.computation.dep_op_handles_by_asset_or_check_key[asset_key]
