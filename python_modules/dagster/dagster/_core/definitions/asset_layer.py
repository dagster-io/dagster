from collections import defaultdict
from typing import TYPE_CHECKING, AbstractSet, Dict, Iterable, Mapping, NamedTuple, Optional, Set

import dagster._check as check
from dagster._core.definitions.asset_check_spec import AssetCheckKey, AssetCheckSpec

from ..errors import DagsterInvariantViolationError
from .dependency import NodeHandle, NodeInputHandle, NodeOutputHandle
from .events import AssetKey
from .graph_definition import GraphDefinition

if TYPE_CHECKING:
    from dagster._core.definitions.asset_graph import AssetGraph, AssetNode
    from dagster._core.definitions.assets import AssetsDefinition
    from dagster._core.definitions.partition_mapping import PartitionMapping


class AssetLayer(NamedTuple):
    """Stores all of the asset-related information for a Dagster job. Maps each
    input / output in the underlying graph to the asset it represents (if any), and records the
    dependencies between each asset.

    Args:
        asset_key_by_node_input_handle (Mapping[NodeInputHandle, AssetOutputInfo], optional): A mapping
            from a unique input in the underlying graph to the associated AssetKey that it loads from.
        asset_keys_by_node_output_handle (Mapping[NodeOutputHandle, AssetOutputInfo], optional): A mapping
            from a unique output in the underlying graph to the associated AssetOutputInfo.
    """

    asset_graph: "AssetGraph"
    assets_defs_by_node_handle: Mapping[NodeHandle, "AssetsDefinition"]
    asset_keys_by_node_input_handle: Mapping[NodeInputHandle, AssetKey]
    asset_keys_by_node_output_handle: Mapping[NodeOutputHandle, AssetKey]
    check_key_by_node_output_handle: Mapping[NodeOutputHandle, AssetCheckKey]
    node_output_handles_by_asset_check_key: Mapping[AssetCheckKey, NodeOutputHandle]
    check_names_by_asset_key_by_node_handle: Mapping[
        NodeHandle, Mapping[AssetKey, AbstractSet[str]]
    ]

    @staticmethod
    def from_graph_and_assets_node_mapping(
        graph_def: GraphDefinition,
        assets_defs_by_outer_node_handle: Mapping[NodeHandle, "AssetsDefinition"],
        asset_graph: "AssetGraph",
    ) -> "AssetLayer":
        """Generate asset info from a GraphDefinition and a mapping from nodes in that graph to the
        corresponding AssetsDefinition objects.

        Args:
            graph_def (GraphDefinition): The graph for the JobDefinition that we're generating
                this AssetLayer for.
            assets_defs_by_outer_node_handle (Mapping[NodeHandle, AssetsDefinition]): A mapping from
                a NodeHandle pointing to the node in the graph where the AssetsDefinition ended up.
        """
        asset_key_by_input: Dict[NodeInputHandle, AssetKey] = {}
        asset_keys_by_node_output_handle: Dict[NodeOutputHandle, AssetKey] = {}
        check_key_by_output: Dict[NodeOutputHandle, AssetCheckKey] = {}

        node_output_handles_by_asset_check_key: Mapping[AssetCheckKey, NodeOutputHandle] = {}
        check_names_by_asset_key_by_node_handle: Dict[NodeHandle, Dict[AssetKey, Set[str]]] = {}
        assets_defs_by_check_key: Dict[AssetCheckKey, "AssetsDefinition"] = {}

        for node_handle, assets_def in assets_defs_by_outer_node_handle.items():
            for input_name, input_asset_key in assets_def.node_keys_by_input_name.items():
                input_handle = NodeInputHandle(node_handle, input_name)
                asset_key_by_input[input_handle] = input_asset_key
                # resolve graph input to list of op inputs that consume it
                node_input_handles = assets_def.node_def.resolve_input_to_destinations(input_handle)
                for node_input_handle in node_input_handles:
                    asset_key_by_input[node_input_handle] = input_asset_key

            for output_name, asset_key in assets_def.node_keys_by_output_name.items():
                # resolve graph output to the op output it comes from
                inner_output_def, inner_node_handle = assets_def.node_def.resolve_output_to_origin(
                    output_name, handle=node_handle
                )
                node_output_handle = NodeOutputHandle(
                    check.not_none(inner_node_handle), inner_output_def.name
                )

                asset_keys_by_node_output_handle[node_output_handle] = asset_key

                asset_key_by_input.update(
                    {
                        input_handle: asset_key
                        for input_handle in assets_def.node_def.resolve_output_to_destinations(
                            output_name, node_handle
                        )
                    }
                )

            if len(assets_def.check_specs_by_output_name) > 0:
                check_names_by_asset_key_by_node_handle[node_handle] = defaultdict(set)

                for output_name, check_spec in assets_def.check_specs_by_output_name.items():
                    (
                        inner_output_def,
                        inner_node_handle,
                    ) = assets_def.node_def.resolve_output_to_origin(
                        output_name, handle=node_handle
                    )
                    node_output_handle = NodeOutputHandle(
                        check.not_none(inner_node_handle), inner_output_def.name
                    )
                    node_output_handles_by_asset_check_key[check_spec.key] = node_output_handle
                    check_names_by_asset_key_by_node_handle[node_handle][check_spec.asset_key].add(
                        check_spec.name
                    )
                    check_key_by_output[node_output_handle] = check_spec.key

                assets_defs_by_check_key.update({k: assets_def for k in assets_def.check_keys})

        assets_defs_by_op_handle: Dict[NodeHandle, "AssetsDefinition"] = {}
        for outer_node_handle, assets_def in assets_defs_by_outer_node_handle.items():
            if assets_def.computation is not None:
                for op_handle in assets_def.computation.node_def.get_op_handles(
                    parent=outer_node_handle
                ):
                    assets_defs_by_op_handle[op_handle] = assets_def

        return AssetLayer(
            asset_graph=asset_graph,
            asset_keys_by_node_input_handle=asset_key_by_input,
            asset_keys_by_node_output_handle=asset_keys_by_node_output_handle,
            check_key_by_node_output_handle=check_key_by_output,
            assets_defs_by_node_handle=assets_defs_by_op_handle,
            node_output_handles_by_asset_check_key=node_output_handles_by_asset_check_key,
            check_names_by_asset_key_by_node_handle=check_names_by_asset_key_by_node_handle,
        )

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
            for handle, handle_asset_key in self.asset_keys_by_node_output_handle.items()
            if handle_asset_key == asset_key
        ]
        check.invariant(len(matching_handles) == 1)
        return matching_handles[0]

    def assets_def_for_node(self, node_handle: NodeHandle) -> Optional["AssetsDefinition"]:
        return self.assets_defs_by_node_handle.get(node_handle)

    def asset_keys_for_node(self, node_handle: NodeHandle) -> AbstractSet[AssetKey]:
        assets_def = self.assets_def_for_node(node_handle)
        return check.not_none(assets_def).keys

    def asset_key_for_node(self, node_handle: NodeHandle) -> AssetKey:
        asset_keys = self.asset_keys_for_node(node_handle)
        if len(asset_keys) > 1:
            raise DagsterInvariantViolationError(
                "Cannot call `asset_key_for_node` in a multi_asset with more than one asset."
                " Multiple asset keys defined."
            )
        return next(iter(asset_keys))

    def get_spec_for_asset_check(
        self, node_handle: NodeHandle, asset_check_key: AssetCheckKey
    ) -> Optional[AssetCheckSpec]:
        assets_def = self.assets_defs_by_node_handle.get(node_handle)
        return assets_def.get_spec_for_check_key(asset_check_key) if assets_def else None

    def get_output_name_for_asset_check(self, asset_check_key: AssetCheckKey) -> str:
        """Output name in the leaf op."""
        return self.node_output_handles_by_asset_check_key[asset_check_key].output_name

    def asset_key_for_input(self, node_handle: NodeHandle, input_name: str) -> Optional[AssetKey]:
        return self.asset_keys_by_node_input_handle.get(NodeInputHandle(node_handle, input_name))

    def input_for_asset_key(self, node_handle: NodeHandle, key: AssetKey) -> Optional[str]:
        return next(
            (
                input_handle.input_name
                for input_handle, k in self.asset_keys_by_node_input_handle.items()
                if k == key
            ),
            None,
        )

    def asset_key_for_output(self, node_handle: NodeHandle, output_name: str) -> Optional[AssetKey]:
        return self.asset_keys_by_node_output_handle.get(NodeOutputHandle(node_handle, output_name))

    def asset_check_key_for_output(
        self, node_handle: NodeHandle, output_name: str
    ) -> Optional[AssetCheckKey]:
        return self.check_key_by_node_output_handle.get(NodeOutputHandle(node_handle, output_name))

    def partition_mapping_for_node_input(
        self, node_handle: NodeHandle, upstream_asset_key: AssetKey
    ) -> Optional["PartitionMapping"]:
        assets_def = self.assets_defs_by_node_handle.get(node_handle)
        if assets_def is not None:
            return assets_def.get_partition_mapping_for_dep(upstream_asset_key)
        else:
            # Can end up here when a non-asset job has an asset as an input
            return None

    def downstream_dep_assets(self, node_handle: NodeHandle, output_name: str) -> Set[AssetKey]:
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
        assets_def = self.assets_defs_by_node_handle[node_handle]
        return {
            key
            for key in assets_def.asset_or_check_keys_by_dep_op_output_handle[
                NodeOutputHandle(node_handle, output_name)
            ]
            if isinstance(key, AssetKey)
        }

    def upstream_dep_op_handles(self, asset_key: AssetKey) -> AbstractSet[NodeHandle]:
        assets_def = self.asset_graph.get(asset_key).assets_def
        return assets_def.dep_op_handles_by_asset_or_check_key[asset_key]
