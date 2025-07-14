from collections.abc import Iterable, Mapping
from functools import cached_property
from typing import TYPE_CHECKING, AbstractSet, Optional, Sequence, Union  # noqa: UP035

from dagster_shared.record import record

import dagster._check as check
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_key import AssetKey, EntityKey
from dagster._core.definitions.dependency import NodeHandle, NodeInputHandle, NodeOutputHandle
from dagster._core.definitions.graph_definition import GraphDefinition

if TYPE_CHECKING:
    from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
    from dagster._core.definitions.assets.graph.asset_graph import AssetGraph, AssetNode


@record(checked=False)
class AssetLayerData:
    """Data that relates asset-level information to a node in the execution graph."""

    node_handle: NodeHandle
    assets_def: "AssetsDefinition"


@record(checked=False)
class AssetLayer:
    """Stores all of the asset-related information for a Dagster job. Maps execution node data
    to the backing AssetsDefinition, with a variety of convenience methods for common operations.
    """

    data: Sequence[AssetLayerData]
    asset_graph: "AssetGraph"
    # these are set when we have knowledge that a job corresponds to a set
    # of asset keys but don't have any AssetsDefinitions / nodes to map them
    # to. this can happen when we're representing a job that executes in an
    # external system but we don't have a good representation of the nodes
    # contained within it.
    external_job_asset_keys: AbstractSet[AssetKey] = set()
    # these are set when there is additional information that adds mapping
    # information from asset keys to input handles that is not captured by
    # the set of AssetsDefinitions that we have available to us. this can
    # happen when a source asset is used as input to a regular graph.
    mapped_source_asset_keys_by_input_handle: Mapping[NodeInputHandle, AssetKey] = {}

    @property
    def executable_asset_keys(self) -> Iterable[AssetKey]:
        return self.asset_graph.executable_asset_keys

    @cached_property
    def selected_asset_keys(self) -> AbstractSet[AssetKey]:
        return set().union(*(d.assets_def.keys for d in self.data))

    @cached_property
    def _data_by_handle(self) -> Mapping[NodeHandle, AssetLayerData]:
        return {data.node_handle: data for data in self.data}

    @cached_property
    def _data_by_key(self) -> Mapping[EntityKey, AssetLayerData]:
        mapping: dict[EntityKey, AssetLayerData] = {}
        for data in self.data:
            for key in [
                *data.assets_def.keys,
                *(spec.key for spec in data.assets_def.node_check_specs_by_output_name.values()),
            ]:
                mapping[key] = data
        return mapping

    @cached_property
    def _asset_keys_by_inner_input_handle(self) -> Mapping[NodeInputHandle, AssetKey]:
        """A mapping from the inner (op) input handles to the asset key that they
        correspond to.

        This is done with a cached property because there is no way of mapping from
        an inner node handle to the outer graph input handle that it came from, so
        we instead do this as a single bulk operation.
        """
        # seed the dictionary with any additional node inputs that were provided.
        # this is provided when source assets are used as inputs to a regular graph.
        mapping: dict[NodeInputHandle, AssetKey] = dict(
            self.mapped_source_asset_keys_by_input_handle
        )

        for data in self.data:
            assets_def = data.assets_def
            node_def = check.not_none(assets_def.computation).full_node_def
            outer_node_handle = data.node_handle

            # INPUTS: record mapping from outer inputs to inner inputs
            for outer_input_name, key in assets_def.node_keys_by_input_name.items():
                outer_input_handle = NodeInputHandle(
                    node_handle=outer_node_handle, input_name=outer_input_name
                )
                mapping[outer_input_handle] = key
                inner_input_handles = node_def.resolve_input_to_destinations(outer_input_handle)
                for inner_input_handle in inner_input_handles:
                    mapping[inner_input_handle] = key

            # OUTPUTS: record mapping from outer outputs to all inputs that consume them
            for outer_output_name, key in assets_def.node_keys_by_output_name.items():
                # find inputs that consume this output
                input_handles = node_def.resolve_output_to_destinations(
                    output_name=outer_output_name, handle=outer_node_handle
                )
                for outer_input_handle in input_handles:
                    mapping[outer_input_handle] = key
                    # ensure that we map from connected graph inputs to the inner inputs they connect to
                    if isinstance(node_def, GraphDefinition):
                        inner_node = node_def.get_node(outer_input_handle.node_handle.pop())
                        inner_input_handles = inner_node.definition.resolve_input_to_destinations(
                            outer_input_handle
                        )
                        for inner_input_handle in inner_input_handles:
                            mapping[inner_input_handle] = key

        return mapping

    @staticmethod
    def from_mapping(
        assets_defs_by_outer_node_handle: Mapping[NodeHandle, "AssetsDefinition"],
        asset_graph: "AssetGraph",
    ) -> "AssetLayer":
        return AssetLayer(
            data=[
                AssetLayerData(node_handle=node_handle, assets_def=assets_def)
                for node_handle, assets_def in assets_defs_by_outer_node_handle.items()
            ],
            asset_graph=asset_graph,
        )

    @staticmethod
    def for_external_job(asset_keys: Iterable[AssetKey]) -> "AssetLayer":
        from dagster._core.definitions.assets.graph.asset_graph import AssetGraph

        return AssetLayer(
            data=[], asset_graph=AssetGraph.from_assets([]), external_job_asset_keys=set(asset_keys)
        )

    def get(self, asset_key: AssetKey) -> "AssetNode":
        return self.asset_graph.get(asset_key)

    def has(self, asset_key: AssetKey) -> bool:
        return self.asset_graph.has(asset_key)

    def _maybe_get_data(self, ptr: Union[NodeHandle, EntityKey]) -> Optional[AssetLayerData]:
        if isinstance(ptr, NodeHandle):
            # we need to ensure that the node handle we use for the lookup is the **outer**
            # node handle when in the context of a graph asset.
            while ptr.parent is not None:
                ptr = ptr.parent
            return self._data_by_handle.get(ptr)
        else:
            return self._data_by_key.get(ptr)

    def _get_data(self, ptr: Union[NodeHandle, EntityKey]) -> AssetLayerData:
        return check.not_none(self._maybe_get_data(ptr), f"Could not find AssetLayerData for {ptr}")

    def get_op_output_handle(self, key: EntityKey) -> NodeOutputHandle:
        data = self._get_data(key)
        computation = check.not_none(data.assets_def.computation)
        # the outer node handle that we store may refer to a graph definition,
        # so ensure that we resolve the output to the actual op output
        output_name = computation.output_names_by_entity_key[key]
        inner_output_def, inner_node_handle = computation.node_def.resolve_output_to_origin(
            output_name, data.node_handle
        )
        return NodeOutputHandle(node_handle=inner_node_handle, output_name=inner_output_def.name)

    def get_assets_def_for_node(self, node_handle: NodeHandle) -> Optional["AssetsDefinition"]:
        data = self._maybe_get_data(node_handle)
        return data.assets_def if data else None

    def get_selected_entity_keys_for_node(self, node_handle: NodeHandle) -> AbstractSet[EntityKey]:
        data = self._maybe_get_data(node_handle)
        return data.assets_def.asset_and_check_keys if data else set()

    def get_asset_key_for_node(self, node_handle: NodeHandle) -> AssetKey:
        return self._get_data(node_handle).assets_def.key

    def get_op_output_name(self, key: EntityKey) -> str:
        return self.get_op_output_handle(key).output_name

    def get_node_input_name(self, node_handle: NodeHandle, key: AssetKey) -> Optional[str]:
        data = self._maybe_get_data(node_handle)
        return data.assets_def.input_names_by_node_key.get(key) if data else None

    def get_entity_key_for_node_output(
        self, inner_node_handle: NodeHandle, output_name: str
    ) -> Optional[EntityKey]:
        data = self._maybe_get_data(inner_node_handle)
        if data is None:
            return None
        computation = check.not_none(data.assets_def.computation)
        return computation.entity_keys_by_op_output_handle.get(
            NodeOutputHandle(node_handle=inner_node_handle.pop(), output_name=output_name)
        )

    def get_asset_key_for_node_output(
        self, node_handle: NodeHandle, output_name: str
    ) -> Optional[AssetKey]:
        key = self.get_entity_key_for_node_output(node_handle, output_name)
        return key if isinstance(key, AssetKey) else None

    def get_asset_check_key_for_node_output(
        self, node_handle: NodeHandle, output_name: str
    ) -> Optional[AssetCheckKey]:
        key = self.get_entity_key_for_node_output(node_handle, output_name)
        return key if isinstance(key, AssetCheckKey) else None

    def get_asset_key_for_node_input(
        self, inner_node_handle: NodeHandle, input_name: str
    ) -> Optional[AssetKey]:
        node_input_handle = NodeInputHandle(node_handle=inner_node_handle, input_name=input_name)
        return self._asset_keys_by_inner_input_handle.get(node_input_handle)

    def downstream_dep_assets_and_checks(
        self, node_handle: NodeHandle, output_name: str
    ) -> set[EntityKey]:
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
        assets_def = self._get_data(node_handle).assets_def
        return {
            key
            for key in check.not_none(assets_def.computation).entity_keys_by_dep_op_output_handle[
                NodeOutputHandle(node_handle=node_handle.pop(), output_name=output_name)
            ]
        }

    def upstream_dep_op_handles(self, asset_key: AssetKey) -> AbstractSet[NodeHandle]:
        data = self._get_data(asset_key)
        computation = check.not_none(data.assets_def.computation)
        op_handles_in_assets_def = computation.dep_op_handles_by_entity_key[asset_key]
        outer_node_handle = NodeHandle(data.node_handle.name, parent=None)
        return {outer_node_handle.with_child(op_handle) for op_handle in op_handles_in_assets_def}
