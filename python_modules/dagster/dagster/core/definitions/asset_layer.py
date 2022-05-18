from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Callable,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

import dagster._check as check
from dagster.core.definitions.events import AssetKey
from dagster.core.selector.subset_selector import AssetSelectionData

from .dependency import NodeHandle, NodeInputHandle, NodeOutputHandle
from .graph_definition import GraphDefinition
from .node_definition import NodeDefinition

if TYPE_CHECKING:
    from dagster.core.asset_defs import AssetGroup, AssetsDefinition
    from dagster.core.execution.context.output import OutputContext

    from .job_definition import JobDefinition
    from .partition import PartitionsDefinition


class AssetOutputInfo(
    NamedTuple(
        "_AssetOutputInfo",
        [
            ("key", AssetKey),
            ("partitions_fn", Callable[["OutputContext"], Optional[AbstractSet[str]]]),
            ("partitions_def", Optional["PartitionsDefinition"]),
            ("is_required", bool),
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
        is_required: bool = True,
    ):
        return super().__new__(
            cls,
            key=check.inst_param(key, "key", AssetKey),
            partitions_fn=check.opt_callable_param(partitions_fn, "partitions_fn", lambda _: None),
            partitions_def=partitions_def,
            is_required=is_required,
        )


def _resolve_input_to_destinations(
    name: str, node_def: NodeDefinition, handle: NodeHandle
) -> Sequence[NodeInputHandle]:
    """
    Recursively follow input mappings to find all op inputs for a graph input.
    """
    if not isinstance(node_def, GraphDefinition):
        # must be in the op definition
        return [NodeInputHandle(node_handle=handle, input_name=name)]
    all_destinations: List[NodeInputHandle] = []
    for mapping in node_def.input_mappings:
        if mapping.definition.name != name:
            continue
        # recurse into graph structure
        all_destinations += _resolve_input_to_destinations(
            # update name to be the mapped input name
            name=mapping.maps_to.input_name,
            node_def=node_def.solid_named(mapping.maps_to.solid_name).definition,
            handle=NodeHandle(mapping.maps_to.solid_name, parent=handle),
        )
    return all_destinations


def _build_graph_dependencies(
    graph_def: GraphDefinition,
    parent_handle: Union[NodeHandle, None],
    outputs_by_graph_handle: Dict[NodeHandle, Dict[str, NodeOutputHandle]],
    non_asset_inputs_by_node_handle: Dict[NodeHandle, Sequence[NodeOutputHandle]],
    assets_defs_by_node_handle: Mapping[NodeHandle, "AssetsDefinition"],
):
    """
    Scans through every node in the graph, making a recursive call when a node is a graph.

    Builds two dictionaries:

    outputs_by_graph_handle: A mapping of every graph node handle to a dictionary with each out
        name as a key and a NodeOutputHandle containing the op output name and op node handle

    non_asset_inputs_by_node_handle: A mapping of all node handles to all upstream node handles
        that are not assets. Each key is a node output handle.
    """
    dep_struct = graph_def.dependency_structure
    for sub_node_name, sub_node in graph_def.node_dict.items():
        curr_node_handle = NodeHandle(sub_node_name, parent=parent_handle)
        if isinstance(sub_node.definition, GraphDefinition):
            _build_graph_dependencies(
                sub_node.definition,
                curr_node_handle,
                outputs_by_graph_handle,
                non_asset_inputs_by_node_handle,
                assets_defs_by_node_handle,
            )
            outputs_by_graph_handle[curr_node_handle] = {
                mapping.definition.name: NodeOutputHandle(
                    NodeHandle(mapping.maps_from.solid_name, parent=curr_node_handle),
                    mapping.maps_from.output_name,
                )
                for mapping in sub_node.definition.output_mappings
            }
        non_asset_inputs_by_node_handle[curr_node_handle] = [
            NodeOutputHandle(
                NodeHandle(output_handle.solid_name, parent=parent_handle),
                output_handle.output_def.name,
            )
            for output_handle in dep_struct.all_upstream_outputs_from_solid(sub_node_name)
            if NodeHandle(output_handle.solid.name, parent=parent_handle)
            not in assets_defs_by_node_handle
        ]


def _get_dependency_node_handles(
    non_asset_inputs_by_node_handle: Mapping[NodeHandle, Sequence[NodeOutputHandle]],
    outputs_by_graph_handle: Mapping[NodeHandle, Mapping[str, NodeOutputHandle]],
    dep_node_handles_by_node: Dict[NodeHandle, List[NodeHandle]],
    node_output_handle: NodeOutputHandle,
) -> Sequence[NodeHandle]:
    """
    Given a node handle and an optional output name of the node (if the node is a graph), return
    all upstream op node handles (leaf nodes).

    Arguments:

    outputs_by_graph_handle: A mapping of every graph node handle to a dictionary with each out
        name as a key and a NodeOutputHandle containing the op output name and op node handle
    non_asset_inputs_by_node_handle: A mapping of all node handles to all upstream node handles
        that are not assets. Each key is a node output handle.
    dep_node_handles_by_node: A mapping of each non-graph node to all non-graph node dependencies.
        Used for memoization to avoid scanning already visited nodes.
    curr_node_handle: The current node handle being traversed.
    graph_output_name: Name of the node output being traversed. Only used if the current node is a
        graph to trace the op that generates this output.
    """
    curr_node_handle = node_output_handle.node_handle

    if curr_node_handle in dep_node_handles_by_node:
        return dep_node_handles_by_node[curr_node_handle]

    dependency_node_handles: List[
        NodeHandle
    ] = []  # first node in list is node that outputs the asset
    if curr_node_handle not in outputs_by_graph_handle:
        dependency_node_handles.append(curr_node_handle)
    else:  # is graph
        node_output_handle = outputs_by_graph_handle[curr_node_handle][
            node_output_handle.output_name
        ]
        dependency_node_handles.extend(
            _get_dependency_node_handles(
                non_asset_inputs_by_node_handle,
                outputs_by_graph_handle,
                dep_node_handles_by_node,
                node_output_handle,
            )
        )
    for node_output_handle in non_asset_inputs_by_node_handle[curr_node_handle]:
        dependency_node_handles.extend(
            _get_dependency_node_handles(
                non_asset_inputs_by_node_handle,
                outputs_by_graph_handle,
                dep_node_handles_by_node,
                node_output_handle,
            )
        )

    if curr_node_handle not in outputs_by_graph_handle:
        dep_node_handles_by_node[curr_node_handle] = dependency_node_handles

    return dependency_node_handles


def _asset_key_to_dep_node_handles(
    graph_def: GraphDefinition, assets_defs_by_node_handle: Mapping[NodeHandle, "AssetsDefinition"]
) -> Mapping[AssetKey, Set[NodeHandle]]:
    """
    For each asset in assets_defs_by_node_handle, returns all the op handles within the asset's node
    that are upstream dependencies of the asset.
    """
    # A mapping of all node handles to all upstream node handles
    # that are not assets. Each key is a node handle with node output handle value
    non_asset_inputs_by_node_handle: Dict[NodeHandle, Sequence[NodeOutputHandle]] = {}

    # A mapping of every graph node handle to a dictionary with each out
    # name as a key and node output handle value
    outputs_by_graph_handle: Dict[NodeHandle, Dict[str, NodeOutputHandle]] = {}
    _build_graph_dependencies(
        graph_def=graph_def,
        parent_handle=None,
        outputs_by_graph_handle=outputs_by_graph_handle,
        non_asset_inputs_by_node_handle=non_asset_inputs_by_node_handle,
        assets_defs_by_node_handle=assets_defs_by_node_handle,
    )

    dep_nodes_by_asset_key: Dict[AssetKey, List[NodeHandle]] = {}

    for node_handle, assets_defs in assets_defs_by_node_handle.items():
        dep_node_handles_by_node: Dict[
            NodeHandle, List[NodeHandle]
        ] = {}  # memoized map of nodehandle to all node handle dependencies that are ops
        for output_name, asset_key in assets_defs.node_asset_keys_by_output_name.items():
            output_def = assets_defs.node_def.output_def_named(output_name)
            output_name = output_def.name

            dep_nodes_by_asset_key[
                asset_key
            ] = []  # first element in list is node that outputs asset
            if node_handle not in outputs_by_graph_handle:
                dep_nodes_by_asset_key[asset_key].extend([node_handle])
            else:  # is graph
                node_output_handle = outputs_by_graph_handle[node_handle][output_name]
                dep_nodes_by_asset_key[asset_key].extend(
                    _get_dependency_node_handles(
                        non_asset_inputs_by_node_handle,
                        outputs_by_graph_handle,
                        dep_node_handles_by_node,
                        node_output_handle,
                    )
                )

    # handle internal_asset_deps
    for node_handle, assets_defs in assets_defs_by_node_handle.items():
        all_output_asset_keys = assets_defs.asset_keys
        for asset_key, dep_asset_keys in assets_defs.asset_deps.items():
            for dep_asset_key in [key for key in dep_asset_keys if key in all_output_asset_keys]:
                output_node = dep_nodes_by_asset_key[asset_key][
                    0
                ]  # first item in list is the original node that outputted the asset
                dep_asset_key_node_handles = [
                    node for node in dep_nodes_by_asset_key[dep_asset_key] if node != output_node
                ]
                dep_nodes_by_asset_key[asset_key] = [
                    node
                    for node in dep_nodes_by_asset_key[asset_key]
                    if node not in dep_asset_key_node_handles
                ]

    dep_node_set_by_asset_key: Dict[AssetKey, Set[NodeHandle]] = {}
    for asset_key, dep_node_handles in dep_nodes_by_asset_key.items():
        dep_node_set_by_asset_key[asset_key] = set(dep_node_handles)
    return dep_node_set_by_asset_key


def _asset_mappings_for_node(
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
                input_handle = NodeInputHandle(node_handle=node_handle, input_name=input_def.name)
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
            n_asset_key_by_input, n_asset_info_by_output, n_asset_deps = _asset_mappings_for_node(
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
        asset_keys_by_node_input_handle: Optional[Mapping[NodeInputHandle, AssetKey]] = None,
        asset_info_by_node_output_handle: Optional[
            Mapping[NodeOutputHandle, AssetOutputInfo]
        ] = None,
        asset_deps: Optional[Mapping[AssetKey, AbstractSet[AssetKey]]] = None,
        dependency_node_handles_by_asset_key: Optional[Mapping[AssetKey, Set[NodeHandle]]] = None,
        assets_defs: Optional[List["AssetsDefinition"]] = None,
    ):
        self._asset_keys_by_node_input_handle = check.opt_dict_param(
            asset_keys_by_node_input_handle,
            "asset_keys_by_node_input_handle",
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
        self._dependency_node_handles_by_asset_key = check.opt_dict_param(
            dependency_node_handles_by_asset_key,
            "dependency_node_handles_by_asset_key",
            key_type=AssetKey,
            value_type=Set,
        )
        self._assets_defs = check.opt_list_param(assets_defs, "assets_defs")

        # keep an index from node handle to all keys expected to be generated in that node
        self._asset_keys_by_node_handle: Dict[NodeHandle, Set[AssetKey]] = defaultdict(set)
        for node_output_handle, asset_info in self._asset_info_by_node_output_handle.items():
            if asset_info.is_required:
                self._asset_keys_by_node_handle[node_output_handle.node_handle].add(asset_info.key)

    @staticmethod
    def from_graph(graph_def: GraphDefinition) -> "AssetLayer":
        """Scrape asset info off of InputDefinition/OutputDefinition instances"""
        check.inst_param(graph_def, "graph_def", GraphDefinition)
        asset_by_input, asset_by_output, asset_deps = _asset_mappings_for_node(graph_def, None)
        return AssetLayer(
            asset_keys_by_node_input_handle=asset_by_input,
            asset_info_by_node_output_handle=asset_by_output,
            asset_deps=asset_deps,
        )

    @staticmethod
    def from_graph_and_assets_node_mapping(
        graph_def: GraphDefinition,
        assets_defs_by_node_handle: Mapping[NodeHandle, "AssetsDefinition"],
    ) -> "AssetLayer":
        """
        Generate asset info from a GraphDefinition and a mapping from nodes in that graph to the
        corresponding AssetsDefinition objects.

        Args:
            graph_def (GraphDefinition): The graph for the JobDefinition that we're generating
                this AssetLayer for.
            assets_defs_by_node_handle (Mapping[NodeHandle, AssetsDefinition]): A mapping from
                a NodeHandle pointing to the node in the graph where the AssetsDefinition ended up.
        """
        check.inst_param(graph_def, "graph_def", GraphDefinition)
        check.dict_param(
            assets_defs_by_node_handle, "assets_defs_by_node_handle", key_type=NodeHandle
        )

        asset_key_by_input: Dict[NodeInputHandle, AssetKey] = {}
        asset_info_by_output: Dict[NodeOutputHandle, AssetOutputInfo] = {}
        asset_deps: Dict[AssetKey, AbstractSet[AssetKey]] = {}
        for node_handle, assets_def in assets_defs_by_node_handle.items():
            asset_deps.update(assets_def.asset_deps)

            for input_name, asset_key in assets_def.node_asset_keys_by_input_name.items():
                # resolve graph input to list of op inputs that consume it
                node_input_handles = _resolve_input_to_destinations(
                    input_name, assets_def.node_def, node_handle
                )
                for node_input_handle in node_input_handles:
                    asset_key_by_input[node_input_handle] = asset_key

            for output_name, asset_key in assets_def.node_asset_keys_by_output_name.items():
                # resolve graph output to the op output it comes from
                inner_output_def, inner_node_handle = assets_def.node_def.resolve_output_to_origin(
                    output_name, handle=node_handle
                )
                node_output_handle = NodeOutputHandle(inner_node_handle, inner_output_def.name)
                partition_fn = lambda context: {context.partition_key}
                asset_info_by_output[node_output_handle] = AssetOutputInfo(
                    asset_key,
                    partitions_fn=partition_fn if assets_def.partitions_def else None,
                    partitions_def=assets_def.partitions_def,
                    is_required=asset_key in assets_def.asset_keys,
                )
        return AssetLayer(
            asset_keys_by_node_input_handle=asset_key_by_input,
            asset_info_by_node_output_handle=asset_info_by_output,
            asset_deps=asset_deps,
            dependency_node_handles_by_asset_key=_asset_key_to_dep_node_handles(
                graph_def, assets_defs_by_node_handle
            ),
            assets_defs=[assets_def for assets_def in assets_defs_by_node_handle.values()],
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

    @property
    def dependency_node_handles_by_asset_key(self) -> Mapping[AssetKey, Sequence[NodeOutputHandle]]:
        return self._dependency_node_handles_by_asset_key

    @property
    def asset_keys(self) -> Iterable[AssetKey]:
        return self._dependency_node_handles_by_asset_key.keys()

    def asset_keys_for_node(self, node_handle: NodeHandle) -> AbstractSet[AssetKey]:
        return self._asset_keys_by_node_handle[node_handle]

    def asset_key_for_input(self, node_handle: NodeHandle, input_name: str) -> Optional[AssetKey]:
        return self._asset_keys_by_node_input_handle.get(NodeInputHandle(node_handle, input_name))

    def asset_info_for_output(
        self, node_handle: NodeHandle, output_name: str
    ) -> Optional[AssetOutputInfo]:
        return self._asset_info_by_node_output_handle.get(
            NodeOutputHandle(node_handle, output_name)
        )


def build_asset_selection_job(
    job_to_subselect: "JobDefinition",
    asset_selection: FrozenSet[AssetKey],
    asset_layer: AssetLayer,
    asset_selection_data: AssetSelectionData,
) -> "JobDefinition":
    from ..asset_defs.asset_group import build_resource_defs
    from ..asset_defs.assets_job import build_assets_job

    check.invariant(
        asset_layer._assets_defs != None,  # pylint:disable=protected-access
        "Asset layer must have _asset_defs argument defined",
    )

    included_assets: List["AssetsDefinition"] = []
    excluded_assets: List["AssetsDefinition"] = []
    for assets_def in asset_layer._assets_defs:  # pylint:disable=protected-access
        if any([asset_key in asset_selection for asset_key in assets_def.asset_keys]):
            included_assets.append(assets_def)
        else:
            excluded_assets.append(assets_def)

    return build_assets_job(
        name=job_to_subselect.name,
        assets=included_assets,
        source_assets=excluded_assets,
        resource_defs=build_resource_defs(job_to_subselect.resource_defs, excluded_assets),
        executor_def=job_to_subselect.executor_def,
        description=job_to_subselect.description,
        tags=job_to_subselect.tags,
        _asset_selection_data=asset_selection_data,
    )
