from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Callable,
    Dict,
    Mapping,
    NamedTuple,
    Optional,
    Set,
    Tuple,
)

from dagster import check
from dagster.core.definitions.events import AssetKey

from .dependency import NodeHandle, NodeInputHandle, NodeOutputHandle
from .graph_definition import GraphDefinition
from .node_definition import NodeDefinition

if TYPE_CHECKING:
    from dagster.core.execution.context.output import OutputContext

    from .partition import PartitionsDefinition


class AssetOutputInfo(
    NamedTuple(
        "_AssetOutputInfo",
        [
            ("key", AssetKey),
            ("partitions_fn", Callable[["OutputContext"], Optional[AbstractSet[str]]]),
            ("partitions_def", Optional["PartitionsDefinition"]),
        ],
    )
):
    """Defines all of the asset-related information for a given output.

    Args:
        key (AssetKey): The AssetKey
        partitions_fn (OutputContext -> Optional[Set[str]], optional): A function which takes the
            current OutputContext and generates a set of partition names that will be materialized
            for this asset.
        partitions_def (PartitionsDefinition, optional): Defines the set of valid partitions
            for this asset.
    """

    def __new__(
        cls,
        key: AssetKey,
        partitions_fn: Optional[Callable[["OutputContext"], Optional[AbstractSet[str]]]] = None,
        partitions_def: Optional["PartitionsDefinition"] = None,
    ):
        return super().__new__(
            cls,
            key=check.inst_param(key, "key", AssetKey),
            partitions_fn=check.opt_callable_param(partitions_fn, "partitions_fn", lambda _: None),
            partitions_def=partitions_def,
        )


def _assets_job_info_for_node(
    node_def: NodeDefinition, node_handle: Optional[NodeHandle]
) -> Tuple[
    Mapping[NodeInputHandle, AssetKey],
    Mapping[NodeOutputHandle, AssetOutputInfo],
    Mapping[AssetKey, AbstractSet[AssetKey]],
]:
    """
    Recursively iterate through all the sub-nodes of a Node to find any ops with asset info
    encoded on their inputs/outputs
    """
    check.inst_param(node_def, "node_def", NodeDefinition)
    check.opt_inst_param(node_handle, "node_handle", NodeHandle)

    asset_key_by_input: Dict[NodeInputHandle, AssetKey] = {}
    asset_info_by_output: Dict[NodeOutputHandle, AssetOutputInfo] = {}
    asset_deps: Dict[AssetKey, AbstractSet[AssetKey]] = {}
    if not isinstance(node_def, GraphDefinition):
        # must be in an op (or solid)
        if node_handle is None:
            check.failed("Must have node_handle for non-graph NodeDefinition")

        input_asset_keys: Set[AssetKey] = set()
        for input_def in node_def.input_defs:
            input_key = input_def.hardcoded_asset_key
            if input_key:
                input_asset_keys.add(input_key)
                input_handle = NodeInputHandle(node_handle, input_def.name)
                asset_key_by_input[input_handle] = input_key

        for output_def in node_def.output_defs:
            output_key = output_def.hardcoded_asset_key
            if output_key:
                output_handle = NodeOutputHandle(node_handle, output_def.name)
                asset_info_by_output[output_handle] = AssetOutputInfo(
                    key=output_key,
                    partitions_fn=output_def.get_asset_partitions,
                    partitions_def=output_def.asset_partitions_def,
                )
                # assume output depends on all inputs
                asset_deps[output_key] = input_asset_keys
    else:
        # keep recursing through structure
        for sub_node_name, sub_node in node_def.node_dict.items():
            n_asset_key_by_input, n_asset_info_by_output, n_asset_deps = _assets_job_info_for_node(
                node_def=sub_node.definition,
                node_handle=NodeHandle(sub_node_name, parent=node_handle),
            )
            asset_key_by_input.update(n_asset_key_by_input)
            asset_info_by_output.update(n_asset_info_by_output)
            asset_deps.update(n_asset_deps)

    return asset_key_by_input, asset_info_by_output, asset_deps


class AssetLayer:
    """
    Stores all of the asset-related information for a Dagster job / pipeline. Maps each
    input / output in the underlying graph to the asset it represents (if any), and records the
    dependencies between each asset.

    Args:
        asset_key_by_node_input_handle (Mapping[NodeInputHandle, AssetOutputInfo], optional): A mapping
            from a unique input in the underlying graph to the associated AssetKey that it loads from.
        asset_info_by_node_output_handle (Mapping[NodeOutputHandle, AssetOutputInfo], optional): A mapping
            from a unique output in the underlying graph to the associated AssetOutputInfo.
        asset_deps (Mapping[AssetKey, AbstractSet[AssetKey]], optional): Records the upstream asset
            keys for each asset key produced by this job.
    """

    def __init__(
        self,
        asset_key_by_node_input_handle: Optional[Mapping[NodeInputHandle, AssetKey]] = None,
        asset_info_by_node_output_handle: Optional[
            Mapping[NodeOutputHandle, AssetOutputInfo]
        ] = None,
        asset_deps: Optional[Mapping[AssetKey, AbstractSet[AssetKey]]] = None,
    ):
        self._asset_key_by_node_input_handle = check.opt_dict_param(
            asset_key_by_node_input_handle,
            "asset_key_by_node_input_handle",
            key_type=NodeInputHandle,
            value_type=AssetKey,
        )
        self._asset_info_by_node_output_handle = check.opt_dict_param(
            asset_info_by_node_output_handle,
            "asset_info_by_node_output_handle",
            key_type=NodeOutputHandle,
            value_type=AssetOutputInfo,
        )
        self._asset_deps = check.opt_dict_param(
            asset_deps, "asset_deps", key_type=AssetKey, value_type=set
        )

    @staticmethod
    def from_graph(graph_def: GraphDefinition) -> "AssetLayer":
        """Scrape asset info off of InputDefinition/OutputDefinition instances"""
        check.inst_param(graph_def, "graph_def", GraphDefinition)
        asset_by_input, asset_by_output, asset_deps = _assets_job_info_for_node(graph_def, None)
        return AssetLayer(
            asset_key_by_node_input_handle=asset_by_input,
            asset_info_by_node_output_handle=asset_by_output,
            asset_deps=asset_deps,
        )

    @property
    def asset_info_by_node_output_handle(self) -> Mapping[NodeOutputHandle, AssetOutputInfo]:
        return self._asset_info_by_node_output_handle

    def upstream_assets_for_asset(self, asset_key: AssetKey) -> AbstractSet[AssetKey]:
        check.invariant(
            asset_key in self._asset_deps,
            "AssetKey '{asset_key}' is not produced by this JobDefinition.",
        )
        return self._asset_deps[asset_key]

    def asset_key_for_input(self, node_handle: NodeHandle, input_name: str) -> Optional[AssetKey]:
        return self._asset_key_by_node_input_handle.get(NodeInputHandle(node_handle, input_name))

    def asset_info_for_output(
        self, node_handle: NodeHandle, output_name: str
    ) -> Optional[AssetOutputInfo]:
        return self._asset_info_by_node_output_handle.get(
            NodeOutputHandle(node_handle, output_name)
        )
