import warnings
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
)

import dagster._check as check
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataUserInput, RawMetadataValue
from dagster._core.selector.subset_selector import AssetSelectionData
from dagster._utils.backcompat import ExperimentalWarning

from ..errors import DagsterInvalidSubsetError
from .config import ConfigMapping
from .dependency import NodeHandle, NodeInputHandle, NodeOutput, NodeOutputHandle
from .events import AssetKey
from .executor_definition import ExecutorDefinition
from .graph_definition import GraphDefinition
from .node_definition import NodeDefinition
from .resource_definition import ResourceDefinition

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition, SourceAsset
    from dagster._core.definitions.job_definition import JobDefinition
    from dagster._core.definitions.resolved_asset_defs import ResolvedAssetDependencies
    from dagster._core.execution.context.output import OutputContext

    from .partition import PartitionedConfig, PartitionsDefinition


class AssetOutputInfo(
    NamedTuple(
        "_AssetOutputInfo",
        [
            ("key", AssetKey),
            ("partitions_fn", Callable[["OutputContext"], Optional[AbstractSet[str]]]),
            ("partitions_def", Optional["PartitionsDefinition"]),
            ("is_required", bool),
            ("code_version", Optional[str]),
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
        code_version (Optional[str], optional): The version of the code that generates this asset.
    """

    def __new__(
        cls,
        key: AssetKey,
        partitions_fn: Optional[Callable[["OutputContext"], Optional[AbstractSet[str]]]] = None,
        partitions_def: Optional["PartitionsDefinition"] = None,
        is_required: bool = True,
        code_version: Optional[str] = None,
    ):
        return super().__new__(
            cls,
            key=check.inst_param(key, "key", AssetKey),
            partitions_fn=check.opt_callable_param(partitions_fn, "partitions_fn", lambda _: None),
            partitions_def=partitions_def,
            is_required=is_required,
            code_version=code_version,
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
        if mapping.graph_input_name != name:
            continue
        # recurse into graph structure
        all_destinations += _resolve_input_to_destinations(
            # update name to be the mapped input name
            name=mapping.maps_to.input_name,
            node_def=node_def.solid_named(mapping.maps_to.solid_name).definition,
            handle=NodeHandle(mapping.maps_to.solid_name, parent=handle),
        )
    return all_destinations


def _resolve_output_to_destinations(
    output_name: str, node_def: NodeDefinition, handle: NodeHandle
) -> Sequence[NodeInputHandle]:
    all_destinations: List[NodeInputHandle] = []
    if not isinstance(node_def, GraphDefinition):
        # must be in the op definition
        return all_destinations

    for mapping in node_def.output_mappings:
        if mapping.graph_output_name != output_name:
            continue
        output_pointer = mapping.maps_from
        output_node = node_def.solid_named(output_pointer.solid_name)

        all_destinations.extend(
            _resolve_output_to_destinations(
                output_pointer.output_name,
                output_node.definition,
                NodeHandle(output_pointer.solid_name, parent=handle),
            )
        )

        output_def = output_node.definition.output_def_named(output_pointer.output_name)
        downstream_input_handles = (
            node_def.dependency_structure.output_to_downstream_inputs_for_node(
                output_pointer.solid_name
            ).get(NodeOutput(output_node, output_def), [])
        )
        for input_handle in downstream_input_handles:
            all_destinations.append(
                NodeInputHandle(
                    NodeHandle(input_handle.solid_name, parent=handle), input_handle.input_name
                )
            )

    return all_destinations


def _build_graph_dependencies(
    graph_def: GraphDefinition,
    parent_handle: Optional[NodeHandle],
    outputs_by_graph_handle: Dict[NodeHandle, Mapping[str, NodeOutputHandle]],
    non_asset_inputs_by_node_handle: Dict[NodeHandle, Sequence[NodeOutputHandle]],
    assets_defs_by_node_handle: Mapping[NodeHandle, "AssetsDefinition"],
) -> None:
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
                mapping.graph_output_name: NodeOutputHandle(
                    NodeHandle(mapping.maps_from.solid_name, parent=curr_node_handle),
                    mapping.maps_from.output_name,
                )
                for mapping in sub_node.definition.output_mappings
            }
        non_asset_inputs_by_node_handle[curr_node_handle] = [
            NodeOutputHandle(
                NodeHandle(node_output.node_name, parent=parent_handle),
                node_output.output_def.name,
            )
            for node_output in dep_struct.all_upstream_outputs_from_node(sub_node_name)
            if NodeHandle(node_output.node.name, parent=parent_handle)
            not in assets_defs_by_node_handle
        ]


def _get_dependency_node_output_handles(
    non_asset_inputs_by_node_handle: Mapping[NodeHandle, Sequence[NodeOutputHandle]],
    outputs_by_graph_handle: Mapping[NodeHandle, Mapping[str, NodeOutputHandle]],
    dep_node_output_handles_by_node_output_handle: Dict[
        NodeOutputHandle, Sequence[NodeOutputHandle]
    ],
    node_output_handle: NodeOutputHandle,
) -> Sequence[NodeOutputHandle]:
    """
    Given a node output handle, return all upstream op node output handles. All node output handles
    belong in the same graph-backed asset node.

    Arguments:

    outputs_by_graph_handle: A mapping of every graph node handle to a dictionary with each out
        name as a key and a NodeOutputHandle containing the op output name and op node handle
    non_asset_inputs_by_node_handle: A mapping of all node handles to all upstream node handles
        that are not assets. Each key is a node output handle.
    dep_node_output_handles_by_node_output_handle: A mapping of each non-graph node output handle
        to all non-graph node output handle dependencies. Used for memoization to avoid scanning
        already visited nodes.
    curr_node_handle: The current node handle being traversed.
    graph_output_name: Name of the node output being traversed. Only used if the current node is a
        graph to trace the op that generates this output.
    """
    curr_node_handle = node_output_handle.node_handle

    if node_output_handle in dep_node_output_handles_by_node_output_handle:
        return dep_node_output_handles_by_node_output_handle[node_output_handle]

    dependency_node_output_handles: List[
        NodeOutputHandle
    ] = []  # first node in list is node output handle that outputs the asset

    if curr_node_handle not in outputs_by_graph_handle:
        dependency_node_output_handles.append(node_output_handle)
    else:  # is graph
        dep_node_output_handle = outputs_by_graph_handle[curr_node_handle][
            node_output_handle.output_name
        ]
        dependency_node_output_handles.extend(
            _get_dependency_node_output_handles(
                non_asset_inputs_by_node_handle,
                outputs_by_graph_handle,
                dep_node_output_handles_by_node_output_handle,
                dep_node_output_handle,
            )
        )
    for dep_node_output_handle in non_asset_inputs_by_node_handle[curr_node_handle]:
        dependency_node_output_handles.extend(
            _get_dependency_node_output_handles(
                non_asset_inputs_by_node_handle,
                outputs_by_graph_handle,
                dep_node_output_handles_by_node_output_handle,
                dep_node_output_handle,
            )
        )

    if curr_node_handle not in outputs_by_graph_handle:
        dep_node_output_handles_by_node_output_handle[
            node_output_handle
        ] = dependency_node_output_handles

    return dependency_node_output_handles


def get_dep_node_handles_of_graph_backed_asset(
    graph_def: GraphDefinition, assets_def: "AssetsDefinition"
) -> Mapping[AssetKey, Set[NodeHandle]]:
    """
    Given a graph-backed asset with graph_def, return a mapping of asset keys outputted by the graph
    to a list of node handles within graph_def that are the dependencies of the asset.

    Arguments:
    graph_def: The graph definition of the graph-backed asset.
    assets_def: The assets definition of the graph-backed asset.

    """
    # asset_key_to_dep_node_handles takes in a graph_def that represents the entire job, where each
    # node is a top-level asset node. Create a dummy graph that wraps around graph_def and pass
    # the dummy graph to asset_key_to_dep_node_handles
    dummy_parent_graph = GraphDefinition("dummy_parent_graph", node_defs=[graph_def])
    dep_node_handles_by_asset_key, _ = asset_key_to_dep_node_handles(
        dummy_parent_graph,
        {NodeHandle(name=graph_def.name, parent=None): assets_def},
    )
    return dep_node_handles_by_asset_key


def asset_key_to_dep_node_handles(
    graph_def: GraphDefinition,
    assets_defs_by_node_handle: Mapping[NodeHandle, "AssetsDefinition"],
) -> Tuple[Mapping[AssetKey, Set[NodeHandle]], Mapping[AssetKey, Sequence[NodeOutputHandle]]]:
    """
    For each asset in assets_defs_by_node_handle, determines all the op handles and output handles
    within the asset's node that are upstream dependencies of the asset.

    Returns a tuple with two objects:
    1. A mapping of each asset key to a set of node handles that are upstream dependencies of the asset.
    2. A mapping of each asset key to a list of node output handles that are upstream dependencies of the asset.

    Arguments:

    graph_def: The graph definition of the job, where each top level node is an asset.
    assets_defs_by_node_handle: A mapping of each node handle to the asset definition for that node.
    """
    # A mapping of all node handles to all upstream node handles
    # that are not assets. Each key is a node handle with node output handle value
    non_asset_inputs_by_node_handle: Dict[NodeHandle, Sequence[NodeOutputHandle]] = {}

    # A mapping of every graph node handle to a dictionary with each out
    # name as a key and node output handle value
    outputs_by_graph_handle: Dict[NodeHandle, Mapping[str, NodeOutputHandle]] = {}
    _build_graph_dependencies(
        graph_def=graph_def,
        parent_handle=None,
        outputs_by_graph_handle=outputs_by_graph_handle,
        non_asset_inputs_by_node_handle=non_asset_inputs_by_node_handle,
        assets_defs_by_node_handle=assets_defs_by_node_handle,
    )

    dep_nodes_by_asset_key: Dict[AssetKey, List[NodeHandle]] = {}
    dep_node_outputs_by_asset_key: Dict[AssetKey, List[NodeOutputHandle]] = {}

    for node_handle, assets_defs in assets_defs_by_node_handle.items():
        dep_node_output_handles_by_node: Dict[
            NodeOutputHandle, Sequence[NodeOutputHandle]
        ] = (
            {}
        )  # memoized map of node output handles to all node output handle dependencies that are from ops
        for output_name, asset_key in assets_defs.keys_by_output_name.items():
            output_def = assets_defs.node_def.output_def_named(output_name)
            output_name = output_def.name

            dep_nodes_by_asset_key[
                asset_key
            ] = []  # first element in list is node that outputs asset

            dep_node_outputs_by_asset_key[asset_key] = []

            if node_handle not in outputs_by_graph_handle:
                dep_nodes_by_asset_key[asset_key].extend([node_handle])
            else:  # is graph
                # node output handle for the given asset key
                node_output_handle = outputs_by_graph_handle[node_handle][output_name]

                dep_node_output_handles = _get_dependency_node_output_handles(
                    non_asset_inputs_by_node_handle,
                    outputs_by_graph_handle,
                    dep_node_output_handles_by_node,
                    node_output_handle,
                )

                dep_node_outputs_by_asset_key[asset_key].extend(dep_node_output_handles)

    # handle internal_asset_deps within graph-backed assets
    for _, assets_def in assets_defs_by_node_handle.items():
        for asset_key, dep_asset_keys in assets_def.asset_deps.items():
            if asset_key not in assets_def.keys:
                continue
            for dep_asset_key in [key for key in dep_asset_keys if key in assets_def.keys]:
                if len(dep_node_outputs_by_asset_key[asset_key]) == 0:
                    # This case occurs when the asset is not yielded from a graph-backed asset
                    continue
                node_output_handle = dep_node_outputs_by_asset_key[asset_key][
                    0
                ]  # first item in list is the original node output handle that outputs the asset
                dep_asset_key_node_output_handles = [
                    output_handle
                    for output_handle in dep_node_outputs_by_asset_key[dep_asset_key]
                    if output_handle != node_output_handle
                ]
                dep_node_outputs_by_asset_key[asset_key] = [
                    node_output
                    for node_output in dep_node_outputs_by_asset_key[asset_key]
                    if node_output not in dep_asset_key_node_output_handles
                ]

    # For graph-backed assets, we've resolved the upstream node output handles dependencies for each
    # node output handle in dep_node_outputs_by_asset_key. We use this to find the upstream
    # node handle dependencies.
    for asset_key, dep_node_outputs in dep_node_outputs_by_asset_key.items():
        dep_nodes_by_asset_key[asset_key].extend(
            [node_output.node_handle for node_output in dep_node_outputs]
        )

    dep_node_set_by_asset_key: Dict[AssetKey, Set[NodeHandle]] = {}
    for asset_key, dep_node_handles in dep_nodes_by_asset_key.items():
        dep_node_set_by_asset_key[asset_key] = set(dep_node_handles)
    return dep_node_set_by_asset_key, dep_node_outputs_by_asset_key


def _asset_mappings_for_node(
    node_def: NodeDefinition, node_handle: Optional[NodeHandle]
) -> Tuple[
    Mapping[NodeInputHandle, AssetKey],
    Mapping[NodeOutputHandle, AssetOutputInfo],
    Mapping[AssetKey, AbstractSet[AssetKey]],
    Mapping[AssetKey, str],
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
    io_manager_by_asset: Dict[AssetKey, str] = {}
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
                    code_version=output_def.code_version,
                )
                # assume output depends on all inputs
                asset_deps[output_key] = input_asset_keys

                io_manager_by_asset[output_key] = output_def.io_manager_key
    else:
        # keep recursing through structure
        for sub_node_name, sub_node in node_def.node_dict.items():
            (
                n_asset_key_by_input,
                n_asset_info_by_output,
                n_asset_deps,
                n_io_manager_by_asset,
            ) = _asset_mappings_for_node(
                node_def=sub_node.definition,
                node_handle=NodeHandle(sub_node_name, parent=node_handle),
            )
            asset_key_by_input.update(n_asset_key_by_input)
            asset_info_by_output.update(n_asset_info_by_output)
            asset_deps.update(n_asset_deps)
            io_manager_by_asset.update(n_io_manager_by_asset)

    return asset_key_by_input, asset_info_by_output, asset_deps, io_manager_by_asset


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

    _asset_keys_by_node_input_handle: Mapping[NodeInputHandle, AssetKey]
    _asset_info_by_node_output_handle: Mapping[NodeOutputHandle, AssetOutputInfo]
    _asset_deps: Mapping[AssetKey, AbstractSet[AssetKey]]
    _dependency_node_handles_by_asset_key: Mapping[AssetKey, Set[NodeHandle]]
    _source_assets_by_key: Mapping[AssetKey, "SourceAsset"]
    _asset_defs_by_key: Mapping[AssetKey, "AssetsDefinition"]
    _asset_defs_by_node_handle: Mapping[NodeHandle, Set["AssetsDefinition"]]
    _io_manager_keys_by_asset_key: Mapping[AssetKey, str]

    def __init__(
        self,
        asset_keys_by_node_input_handle: Optional[Mapping[NodeInputHandle, AssetKey]] = None,
        asset_info_by_node_output_handle: Optional[
            Mapping[NodeOutputHandle, AssetOutputInfo]
        ] = None,
        asset_deps: Optional[Mapping[AssetKey, AbstractSet[AssetKey]]] = None,
        dependency_node_handles_by_asset_key: Optional[Mapping[AssetKey, Set[NodeHandle]]] = None,
        assets_defs: Optional[Sequence["AssetsDefinition"]] = None,
        source_asset_defs: Optional[Sequence["SourceAsset"]] = None,
        io_manager_keys_by_asset_key: Optional[Mapping[AssetKey, str]] = None,
        node_output_handles_to_dep_asset_keys: Optional[
            Mapping[NodeOutputHandle, Set[AssetKey]]
        ] = None,
    ):
        from dagster._core.definitions import SourceAsset

        self._asset_keys_by_node_input_handle = check.opt_mapping_param(
            asset_keys_by_node_input_handle,
            "asset_keys_by_node_input_handle",
            key_type=NodeInputHandle,
            value_type=AssetKey,
        )
        self._asset_info_by_node_output_handle = check.opt_mapping_param(
            asset_info_by_node_output_handle,
            "asset_info_by_node_output_handle",
            key_type=NodeOutputHandle,
            value_type=AssetOutputInfo,
        )
        self._asset_deps = check.opt_mapping_param(
            asset_deps, "asset_deps", key_type=AssetKey, value_type=set
        )
        self._dependency_node_handles_by_asset_key = check.opt_mapping_param(
            dependency_node_handles_by_asset_key,
            "dependency_node_handles_by_asset_key",
            key_type=AssetKey,
            value_type=Set,
        )
        self._source_assets_by_key = {
            source_asset.key: source_asset
            for source_asset in check.opt_sequence_param(
                source_asset_defs, "source_assets_defs", of_type=SourceAsset
            )
        }
        self._assets_defs_by_key = {
            key: assets_def
            for assets_def in check.opt_sequence_param(assets_defs, "assets_defs")
            for key in assets_def.keys
        }

        # keep an index from node handle to the AssetsDefinition for that node
        self._assets_defs_by_node_handle: Dict[NodeHandle, "AssetsDefinition"] = {}
        for asset_key, node_handles in self._dependency_node_handles_by_asset_key.items():
            for node_handle in node_handles:
                self._assets_defs_by_node_handle[node_handle] = self._assets_defs_by_key[asset_key]

        self._io_manager_keys_by_asset_key = check.opt_mapping_param(
            io_manager_keys_by_asset_key,
            "io_manager_keys_by_asset_key",
            key_type=AssetKey,
            value_type=str,
        )

        # Used to store the asset key dependencies of op node handles within graph backed assets
        # See AssetLayer.downstream_dep_assets for more information
        self._node_output_handle_to_dep_asset_keys = check.opt_mapping_param(
            node_output_handles_to_dep_asset_keys,
            "node_output_handles_to_dep_asset_keys",
            key_type=NodeOutputHandle,
            value_type=set,
        )

    @staticmethod
    def from_graph(graph_def: GraphDefinition) -> "AssetLayer":
        """Scrape asset info off of InputDefinition/OutputDefinition instances"""
        check.inst_param(graph_def, "graph_def", GraphDefinition)
        asset_by_input, asset_by_output, asset_deps, io_manager_by_asset = _asset_mappings_for_node(
            graph_def, None
        )
        return AssetLayer(
            asset_keys_by_node_input_handle=asset_by_input,
            asset_info_by_node_output_handle=asset_by_output,
            asset_deps=asset_deps,
            io_manager_keys_by_asset_key=io_manager_by_asset,
        )

    @staticmethod
    def from_graph_and_assets_node_mapping(
        graph_def: GraphDefinition,
        assets_defs_by_node_handle: Mapping[NodeHandle, "AssetsDefinition"],
        source_assets: Sequence["SourceAsset"],
        resolved_asset_deps: "ResolvedAssetDependencies",
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
        check.mapping_param(
            assets_defs_by_node_handle, "assets_defs_by_node_handle", key_type=NodeHandle
        )
        asset_key_by_input: Dict[NodeInputHandle, AssetKey] = {}
        asset_info_by_output: Dict[NodeOutputHandle, AssetOutputInfo] = {}
        asset_deps: Dict[AssetKey, AbstractSet[AssetKey]] = {}
        io_manager_by_asset: Dict[AssetKey, str] = {
            source_asset.key: source_asset.get_io_manager_key() for source_asset in source_assets
        }

        (
            dep_node_handles_by_asset_key,
            dep_node_output_handles_by_asset_key,
        ) = asset_key_to_dep_node_handles(graph_def, assets_defs_by_node_handle)

        for node_handle, assets_def in assets_defs_by_node_handle.items():
            for key in assets_def.keys:
                asset_deps[key] = resolved_asset_deps.get_resolved_upstream_asset_keys(
                    assets_def, key
                )

            for input_name in assets_def.node_keys_by_input_name.keys():
                resolved_asset_key = resolved_asset_deps.get_resolved_asset_key_for_input(
                    assets_def, input_name
                )
                asset_key_by_input[NodeInputHandle(node_handle, input_name)] = resolved_asset_key
                # resolve graph input to list of op inputs that consume it
                node_input_handles = _resolve_input_to_destinations(
                    input_name, assets_def.node_def, node_handle
                )
                for node_input_handle in node_input_handles:
                    asset_key_by_input[node_input_handle] = resolved_asset_key

            for output_name, asset_key in assets_def.node_keys_by_output_name.items():
                # resolve graph output to the op output it comes from
                inner_output_def, inner_node_handle = assets_def.node_def.resolve_output_to_origin(
                    output_name, handle=node_handle
                )
                node_output_handle = NodeOutputHandle(
                    check.not_none(inner_node_handle), inner_output_def.name
                )

                def partitions_fn(context: "OutputContext") -> AbstractSet[str]:
                    from dagster._core.definitions.partition import PartitionsDefinition

                    if context.has_partition_key:
                        return {context.partition_key}

                    return set(
                        cast(
                            PartitionsDefinition, context.asset_partitions_def
                        ).get_partition_keys_in_range(context.asset_partition_key_range)
                    )

                asset_info_by_output[node_output_handle] = AssetOutputInfo(
                    asset_key,
                    partitions_fn=partitions_fn if assets_def.partitions_def else None,
                    partitions_def=assets_def.partitions_def,
                    is_required=asset_key in assets_def.keys,
                    code_version=inner_output_def.code_version,
                )
                io_manager_by_asset[asset_key] = inner_output_def.io_manager_key

                asset_key_by_input.update(
                    {
                        input_handle: asset_key
                        for input_handle in _resolve_output_to_destinations(
                            output_name, assets_def.node_def, node_handle
                        )
                    }
                )

        node_output_handles_to_dep_asset_keys = defaultdict(set)
        for asset_key, node_output_handles in dep_node_output_handles_by_asset_key.items():
            for node_output_handle in node_output_handles:
                node_output_handles_to_dep_asset_keys[node_output_handle].add(asset_key)

        return AssetLayer(
            asset_keys_by_node_input_handle=asset_key_by_input,
            asset_info_by_node_output_handle=asset_info_by_output,
            asset_deps=asset_deps,
            dependency_node_handles_by_asset_key=dep_node_handles_by_asset_key,
            assets_defs=[assets_def for assets_def in assets_defs_by_node_handle.values()],
            source_asset_defs=source_assets,
            io_manager_keys_by_asset_key=io_manager_by_asset,
            node_output_handles_to_dep_asset_keys=node_output_handles_to_dep_asset_keys,
        )

    @property
    def asset_info_by_node_output_handle(self) -> Mapping[NodeOutputHandle, AssetOutputInfo]:
        return self._asset_info_by_node_output_handle

    @property
    def io_manager_keys_by_asset_key(self) -> Mapping[AssetKey, str]:
        return self._io_manager_keys_by_asset_key

    def upstream_assets_for_asset(self, asset_key: AssetKey) -> AbstractSet[AssetKey]:
        check.invariant(
            asset_key in self._asset_deps,
            "AssetKey '{asset_key}' is not produced by this JobDefinition.",
        )
        return self._asset_deps[asset_key]

    @property
    def dependency_node_handles_by_asset_key(self) -> Mapping[AssetKey, AbstractSet[NodeHandle]]:
        return self._dependency_node_handles_by_asset_key

    @property
    def asset_keys(self) -> Iterable[AssetKey]:
        return self._dependency_node_handles_by_asset_key.keys()

    @property
    def source_assets_by_key(self) -> Mapping[AssetKey, "SourceAsset"]:
        return self._source_assets_by_key

    @property
    def assets_defs_by_key(self) -> Mapping[AssetKey, "AssetsDefinition"]:
        return self._assets_defs_by_key

    @property
    def has_assets_defs(self) -> bool:
        return len(self.assets_defs_by_key) > 0

    def assets_def_for_asset(self, asset_key: AssetKey) -> "AssetsDefinition":
        return self._assets_defs_by_key[asset_key]

    def assets_def_for_node(self, node_handle: NodeHandle) -> Optional["AssetsDefinition"]:
        return self._assets_defs_by_node_handle.get(node_handle)

    def asset_key_for_input(self, node_handle: NodeHandle, input_name: str) -> Optional[AssetKey]:
        return self._asset_keys_by_node_input_handle.get(NodeInputHandle(node_handle, input_name))

    def io_manager_key_for_asset(self, asset_key: AssetKey) -> str:
        return self._io_manager_keys_by_asset_key.get(asset_key, "io_manager")

    def is_source_for_asset(self, asset_key: AssetKey) -> bool:
        return asset_key in self.source_assets_by_key

    def is_observable_for_asset(self, asset_key: AssetKey) -> bool:
        return (
            asset_key in self.source_assets_by_key
            and self.source_assets_by_key[asset_key].is_observable
        )

    def is_graph_backed_asset(self, asset_key: AssetKey) -> bool:
        assets_def = self.assets_defs_by_key.get(asset_key)
        return False if assets_def is None else isinstance(assets_def.node_def, GraphDefinition)

    def code_version_for_asset(self, asset_key: AssetKey) -> Optional[str]:
        assets_def = self.assets_defs_by_key.get(asset_key)
        if assets_def is not None:
            return assets_def.code_versions_by_key[asset_key]
        else:
            return None

    def metadata_for_asset(self, asset_key: AssetKey) -> Optional[MetadataUserInput]:
        if asset_key in self._source_assets_by_key:
            metadata = self._source_assets_by_key[asset_key].metadata
            return (
                {key: cast(RawMetadataValue, value.value) for key, value in metadata.items()}
                if metadata
                else None
            )
        elif asset_key in self._assets_defs_by_key:
            return self._assets_defs_by_key[asset_key].metadata_by_key[asset_key]
        else:
            check.failed(f"Couldn't find key {asset_key}")

    def asset_info_for_output(
        self, node_handle: NodeHandle, output_name: str
    ) -> Optional[AssetOutputInfo]:
        return self._asset_info_by_node_output_handle.get(
            NodeOutputHandle(node_handle, output_name)
        )

    def group_names_by_assets(self) -> Mapping[AssetKey, str]:
        group_names: Dict[AssetKey, str] = {
            key: assets_def.group_names_by_key[key]
            for key, assets_def in self._assets_defs_by_key.items()
            if key in assets_def.group_names_by_key
        }

        group_names.update(
            {
                key: source_asset_def.group_name
                for key, source_asset_def in self._source_assets_by_key.items()
            }
        )

        return group_names

    def partitions_def_for_asset(self, asset_key: AssetKey) -> Optional["PartitionsDefinition"]:
        assets_def = self._assets_defs_by_key.get(asset_key)

        if assets_def is not None:
            return assets_def.partitions_def
        else:
            source_asset = self._source_assets_by_key.get(asset_key)
            if source_asset is not None:
                return source_asset.partitions_def

        return None

    def downstream_dep_assets(self, node_handle: NodeHandle, output_name: str) -> Set[AssetKey]:
        """
        Given the node handle of an op within a graph-backed asset and an output name,
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
        return self._node_output_handle_to_dep_asset_keys.get(
            NodeOutputHandle(node_handle, output_name), set()
        )


def build_asset_selection_job(
    name: str,
    assets: Iterable["AssetsDefinition"],
    source_assets: Iterable["SourceAsset"],
    executor_def: Optional[ExecutorDefinition] = None,
    config: Optional[Union[ConfigMapping, Mapping[str, Any], "PartitionedConfig"]] = None,
    partitions_def: Optional["PartitionsDefinition"] = None,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    description: Optional[str] = None,
    tags: Optional[Mapping[str, Any]] = None,
    asset_selection: Optional[AbstractSet[AssetKey]] = None,
    asset_selection_data: Optional[AssetSelectionData] = None,
) -> "JobDefinition":
    from dagster._core.definitions.assets_job import (
        build_assets_job,
        build_source_asset_observation_job,
    )

    if asset_selection:
        (included_assets, excluded_assets) = _subset_assets_defs(assets, asset_selection)
        included_source_assets = _subset_source_assets(source_assets, asset_selection)

    else:
        included_assets = list(assets)
        excluded_assets = []
        included_source_assets = []

    if partitions_def:
        for asset in included_assets:
            check.invariant(
                asset.partitions_def == partitions_def or asset.partitions_def is None,
                f"Assets defined for node '{asset.node_def.name}' have a partitions_def of "
                f"{asset.partitions_def}, but job '{name}' has non-matching partitions_def of "
                f"{partitions_def}.",
            )

    # We should disallow simultaneous selection of assets and source assets (but for
    # backcompat we will simply ignore the source asset selection if any regular assets are
    # selected).
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=ExperimentalWarning)
        if len(included_assets) > 0:
            asset_job = build_assets_job(
                name=name,
                assets=included_assets,
                config=config,
                source_assets=[*source_assets, *excluded_assets],
                resource_defs=resource_defs,
                executor_def=executor_def,
                partitions_def=partitions_def,
                description=description,
                tags=tags,
                _asset_selection_data=asset_selection_data,
            )
        else:
            asset_job = build_source_asset_observation_job(
                name=name,
                source_assets=included_source_assets,
                config=config,
                resource_defs=resource_defs,
                executor_def=executor_def,
                partitions_def=partitions_def,
                description=description,
                tags=tags,
                _asset_selection_data=asset_selection_data,
            )

    return asset_job


def _subset_assets_defs(
    assets: Iterable["AssetsDefinition"],
    selected_asset_keys: AbstractSet[AssetKey],
) -> Tuple[Sequence["AssetsDefinition"], Sequence["AssetsDefinition"],]:
    """Given a list of asset key selection queries, generate a set of AssetsDefinition objects
    representing the included/excluded definitions.
    """
    from dagster._core.definitions import AssetsDefinition

    included_assets: Set[AssetsDefinition] = set()
    excluded_assets: Set[AssetsDefinition] = set()

    for asset in set(assets):
        # intersection
        selected_subset = selected_asset_keys & asset.keys
        # all assets in this def are selected
        if selected_subset == asset.keys:
            included_assets.add(asset)
        # no assets in this def are selected
        elif len(selected_subset) == 0:
            excluded_assets.add(asset)
        elif asset.can_subset:
            # subset of the asset that we want
            subset_asset = asset.subset_for(selected_asset_keys)
            included_assets.add(subset_asset)
            # subset of the asset that we don't want
            excluded_assets.add(asset.subset_for(asset.keys - subset_asset.keys))
        else:
            raise DagsterInvalidSubsetError(
                f"When building job, the AssetsDefinition '{asset.node_def.name}' "
                f"contains asset keys {sorted(list(asset.keys))}, but "
                f"attempted to select only {sorted(list(selected_subset))}. "
                "This AssetsDefinition does not support subsetting. Please select all "
                "asset keys produced by this asset."
            )

    return (
        list(included_assets),
        list(excluded_assets),
    )


def _subset_source_assets(
    source_assets: Iterable["SourceAsset"],
    selected_asset_keys: AbstractSet[AssetKey],
) -> Sequence["SourceAsset"]:
    return [
        source_asset for source_asset in source_assets if source_asset.key in selected_asset_keys
    ]
