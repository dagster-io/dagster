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
from dagster._core.definitions.asset_check_spec import AssetCheckKey, AssetCheckSpec
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.hook_definition import HookDefinition
from dagster._core.definitions.metadata import (
    ArbitraryMetadataMapping,
    RawMetadataValue,
)
from dagster._core.selector.subset_selector import AssetSelectionData

from ..errors import (
    DagsterInvalidSubsetError,
    DagsterInvariantViolationError,
)
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
    from dagster._core.definitions.partition_mapping import PartitionMapping
    from dagster._core.definitions.resolved_asset_deps import ResolvedAssetDependencies
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
        output_node = node_def.node_named(output_pointer.node_name)

        all_destinations.extend(
            _resolve_output_to_destinations(
                output_pointer.output_name,
                output_node.definition,
                NodeHandle(output_pointer.node_name, parent=handle),
            )
        )

        output_def = output_node.definition.output_def_named(output_pointer.output_name)
        downstream_input_handles = (
            node_def.dependency_structure.output_to_downstream_inputs_for_node(
                output_pointer.node_name
            ).get(NodeOutput(output_node, output_def), [])
        )
        for input_handle in downstream_input_handles:
            all_destinations.append(
                NodeInputHandle(
                    NodeHandle(input_handle.node_name, parent=handle), input_handle.input_name
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
    """Scans through every node in the graph, making a recursive call when a node is a graph.

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
                    NodeHandle(mapping.maps_from.node_name, parent=curr_node_handle),
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
    """Given a node output handle, return all upstream op node output handles. All node output handles
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

    dependency_node_output_handles: List[NodeOutputHandle] = (
        []
    )  # first node in list is node output handle that outputs the asset

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
        dep_node_output_handles_by_node_output_handle[node_output_handle] = (
            dependency_node_output_handles
        )

    return dependency_node_output_handles


def get_dep_node_handles_of_graph_backed_asset(
    graph_def: GraphDefinition, assets_def: "AssetsDefinition"
) -> Mapping[AssetKey, Set[NodeHandle]]:
    """Given a graph-backed asset with graph_def, return a mapping of asset keys outputted by the graph
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
    """For each asset in assets_defs_by_node_handle, determines all the op handles and output handles
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
        dep_node_output_handles_by_node: Dict[NodeOutputHandle, Sequence[NodeOutputHandle]] = (
            {}
        )  # memoized map of node output handles to all node output handle dependencies that are from ops
        for output_name, asset_key in assets_defs.keys_by_output_name.items():
            dep_nodes_by_asset_key[asset_key] = (
                []
            )  # first element in list is node that outputs asset

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
    for assets_def in assets_defs_by_node_handle.values():
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


class AssetLayer(NamedTuple):
    """Stores all of the asset-related information for a Dagster job. Maps each
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

    assets_defs_by_key: Mapping[AssetKey, "AssetsDefinition"]
    assets_defs_by_node_handle: Mapping[NodeHandle, "AssetsDefinition"]
    asset_keys_by_node_input_handle: Mapping[NodeInputHandle, AssetKey]
    asset_info_by_node_output_handle: Mapping[NodeOutputHandle, AssetOutputInfo]
    check_key_by_node_output_handle: Mapping[NodeOutputHandle, AssetCheckKey]
    asset_deps: Mapping[AssetKey, AbstractSet[AssetKey]]
    dependency_node_handles_by_asset_key: Mapping[AssetKey, Set[NodeHandle]]
    source_assets_by_key: Mapping[AssetKey, "SourceAsset"]
    io_manager_keys_by_asset_key: Mapping[AssetKey, str]
    # Used to store the asset key dependencies of op node handles within graph backed assets
    # See AssetLayer.downstream_dep_assets for more information
    dep_asset_keys_by_node_output_handle: Mapping[NodeOutputHandle, Set[AssetKey]]
    partition_mappings_by_asset_dep: Mapping[Tuple[NodeHandle, AssetKey], "PartitionMapping"]
    asset_checks_defs_by_node_handle: Mapping[NodeHandle, "AssetChecksDefinition"]
    node_output_handles_by_asset_check_key: Mapping[AssetCheckKey, NodeOutputHandle]
    check_names_by_asset_key_by_node_handle: Mapping[
        NodeHandle, Mapping[AssetKey, AbstractSet[str]]
    ]

    @staticmethod
    def from_graph_and_assets_node_mapping(
        graph_def: GraphDefinition,
        assets_defs_by_outer_node_handle: Mapping[NodeHandle, "AssetsDefinition"],
        asset_checks_defs_by_node_handle: Mapping[NodeHandle, "AssetChecksDefinition"],
        source_assets: Sequence["SourceAsset"],
        resolved_asset_deps: "ResolvedAssetDependencies",
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
        asset_info_by_output: Dict[NodeOutputHandle, AssetOutputInfo] = {}
        check_key_by_output: Dict[NodeOutputHandle, AssetCheckKey] = {}
        asset_deps: Dict[AssetKey, AbstractSet[AssetKey]] = {}
        io_manager_by_asset: Dict[AssetKey, str] = {
            source_asset.key: source_asset.get_io_manager_key() for source_asset in source_assets
        }
        partition_mappings_by_asset_dep: Dict[Tuple[NodeHandle, AssetKey], "PartitionMapping"] = {}

        (
            dep_node_handles_by_asset_key,
            dep_node_output_handles_by_asset_key,
        ) = asset_key_to_dep_node_handles(graph_def, assets_defs_by_outer_node_handle)

        node_output_handles_by_asset_check_key: Mapping[AssetCheckKey, NodeOutputHandle] = {}
        check_names_by_asset_key_by_node_handle: Dict[NodeHandle, Dict[AssetKey, Set[str]]] = {}

        for node_handle, assets_def in assets_defs_by_outer_node_handle.items():
            for key in assets_def.keys:
                asset_deps[key] = resolved_asset_deps.get_resolved_upstream_asset_keys(
                    assets_def, key
                )

            for input_name in assets_def.node_keys_by_input_name.keys():
                resolved_asset_key = resolved_asset_deps.get_resolved_asset_key_for_input(
                    assets_def, input_name
                )
                input_handle = NodeInputHandle(node_handle, input_name)
                asset_key_by_input[input_handle] = resolved_asset_key
                # resolve graph input to list of op inputs that consume it
                node_input_handles = assets_def.node_def.resolve_input_to_destinations(input_handle)
                for node_input_handle in node_input_handles:
                    asset_key_by_input[node_input_handle] = resolved_asset_key

                partition_mapping = assets_def.get_partition_mapping_for_input(input_name)
                if partition_mapping is not None:
                    partition_mappings_by_asset_dep[(node_handle, resolved_asset_key)] = (
                        partition_mapping
                    )

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
                        ).get_partition_keys_in_range(
                            context.asset_partition_key_range,
                            dynamic_partitions_store=context.step_context.instance,
                        )
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

            if len(assets_def.check_specs_by_output_name) > 0:
                check_names_by_asset_key_by_node_handle[node_handle] = defaultdict(set)

                for output_name, check_spec in assets_def.check_specs_by_output_name.items():
                    inner_output_def, inner_node_handle = (
                        assets_def.node_def.resolve_output_to_origin(
                            output_name, handle=node_handle
                        )
                    )
                    node_output_handle = NodeOutputHandle(
                        check.not_none(inner_node_handle), inner_output_def.name
                    )
                    node_output_handles_by_asset_check_key[check_spec.key] = node_output_handle
                    check_names_by_asset_key_by_node_handle[node_handle][check_spec.asset_key].add(
                        check_spec.name
                    )
                    check_key_by_output[node_output_handle] = check_spec.key

        dep_asset_keys_by_node_output_handle = defaultdict(set)
        for asset_key, node_output_handles in dep_node_output_handles_by_asset_key.items():
            for node_output_handle in node_output_handles:
                dep_asset_keys_by_node_output_handle[node_output_handle].add(asset_key)

        for node_handle, checks_def in asset_checks_defs_by_node_handle.items():
            check_names_by_asset_key_by_node_handle[node_handle] = defaultdict(set)
            for output_name, check_spec in checks_def.specs_by_output_name.items():
                inner_output_def, inner_node_handle = checks_def.node_def.resolve_output_to_origin(
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

            for input_name, asset_key in checks_def.asset_keys_by_input_name.items():
                input_handle = NodeInputHandle(node_handle, input_name)
                asset_key_by_input[input_handle] = asset_key
                # resolve graph input to list of op inputs that consume it
                node_input_handles = checks_def.node_def.resolve_input_to_destinations(input_handle)
                for node_input_handle in node_input_handles:
                    asset_key_by_input[node_input_handle] = asset_key

        assets_defs_by_key = {
            key: assets_def
            for assets_def in assets_defs_by_outer_node_handle.values()
            for key in assets_def.keys
        }

        source_assets_by_key = {source_asset.key: source_asset for source_asset in source_assets}

        assets_defs_by_node_handle: Dict[NodeHandle, "AssetsDefinition"] = {
            # nodes for assets
            **{
                node_handle: assets_defs_by_key[asset_key]
                for asset_key, node_handles in dep_node_handles_by_asset_key.items()
                for node_handle in node_handles
            },
            # nodes for asset checks. Required for AssetsDefs that have selected checks
            # but not assets
            **{
                node_handle: assets_def
                for node_handle, assets_def in assets_defs_by_outer_node_handle.items()
                if assets_def.check_keys
            },
        }

        return AssetLayer(
            asset_keys_by_node_input_handle=asset_key_by_input,
            asset_info_by_node_output_handle=asset_info_by_output,
            check_key_by_node_output_handle=check_key_by_output,
            asset_deps=asset_deps,
            assets_defs_by_node_handle=assets_defs_by_node_handle,
            dependency_node_handles_by_asset_key=dep_node_handles_by_asset_key,
            assets_defs_by_key=assets_defs_by_key,
            source_assets_by_key=source_assets_by_key,
            io_manager_keys_by_asset_key=io_manager_by_asset,
            dep_asset_keys_by_node_output_handle=dep_asset_keys_by_node_output_handle,
            partition_mappings_by_asset_dep=partition_mappings_by_asset_dep,
            asset_checks_defs_by_node_handle=asset_checks_defs_by_node_handle,
            node_output_handles_by_asset_check_key=node_output_handles_by_asset_check_key,
            check_names_by_asset_key_by_node_handle=check_names_by_asset_key_by_node_handle,
        )

    def upstream_assets_for_asset(self, asset_key: AssetKey) -> AbstractSet[AssetKey]:
        check.invariant(
            asset_key in self.asset_deps,
            "AssetKey '{asset_key}' is not produced by this JobDefinition.",
        )
        return self.asset_deps[asset_key]

    def downstream_assets_for_asset(self, asset_key: AssetKey) -> AbstractSet[AssetKey]:
        return {k for k, v in self.asset_deps.items() if asset_key in v}

    @property
    def asset_keys(self) -> Iterable[AssetKey]:
        return self.dependency_node_handles_by_asset_key.keys()

    @property
    def has_assets_defs(self) -> bool:
        return len(self.assets_defs_by_key) > 0

    @property
    def has_asset_check_defs(self) -> bool:
        return len(self.asset_checks_defs_by_node_handle) > 0

    def has_assets_def_for_asset(self, asset_key: AssetKey) -> bool:
        return asset_key in self.assets_defs_by_key

    def assets_def_for_asset(self, asset_key: AssetKey) -> "AssetsDefinition":
        return self.assets_defs_by_key[asset_key]

    def node_output_handle_for_asset(self, asset_key: AssetKey) -> NodeOutputHandle:
        matching_handles = [
            handle
            for handle, asset_info in self.asset_info_by_node_output_handle.items()
            if asset_info.key == asset_key
        ]
        check.invariant(len(matching_handles) == 1)
        return matching_handles[0]

    def assets_def_for_node(self, node_handle: NodeHandle) -> Optional["AssetsDefinition"]:
        return self.assets_defs_by_node_handle.get(node_handle)

    def asset_key_for_node(self, node_handle: NodeHandle) -> AssetKey:
        assets_def = self.assets_def_for_node(node_handle)
        if not assets_def or len(assets_def.keys_by_output_name.keys()) > 1:
            raise DagsterInvariantViolationError(
                "Cannot call `asset_key_for_node` in a multi_asset with more than one asset."
                " Multiple asset keys defined."
            )
        return next(iter(assets_def.keys_by_output_name.values()))

    def asset_check_specs_for_node(self, node_handle: NodeHandle) -> Sequence[AssetCheckSpec]:
        assets_def_for_node = self.assets_def_for_node(node_handle)
        checks_def_for_node = self.asset_checks_def_for_node(node_handle)

        if assets_def_for_node is not None:
            check.invariant(checks_def_for_node is None)
            return list(assets_def_for_node.check_specs)
        elif checks_def_for_node is not None:
            return list(checks_def_for_node.specs)
        else:
            return []

    def get_spec_for_asset_check(
        self, node_handle: NodeHandle, asset_check_key: AssetCheckKey
    ) -> Optional[AssetCheckSpec]:
        asset_checks_def_or_assets_def = self.asset_checks_defs_by_node_handle.get(
            node_handle
        ) or self.assets_defs_by_node_handle.get(node_handle)
        return (
            asset_checks_def_or_assets_def.get_spec_for_check_key(asset_check_key)
            if asset_checks_def_or_assets_def
            else None
        )

    def get_check_names_by_asset_key_for_node_handle(
        self, node_handle: NodeHandle
    ) -> Mapping[AssetKey, AbstractSet[str]]:
        return self.check_names_by_asset_key_by_node_handle[node_handle]

    def asset_checks_def_for_node(
        self, node_handle: NodeHandle
    ) -> Optional["AssetChecksDefinition"]:
        return self.asset_checks_defs_by_node_handle.get(node_handle)

    @property
    def asset_checks_defs(self) -> Iterable[AssetChecksDefinition]:
        return self.asset_checks_defs_by_node_handle.values()

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

    def io_manager_key_for_asset(self, asset_key: AssetKey) -> str:
        return self.io_manager_keys_by_asset_key.get(asset_key, "io_manager")

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

    def metadata_for_asset(
        self, asset_key: AssetKey
    ) -> Optional[Mapping[str, ArbitraryMetadataMapping]]:
        if asset_key in self.source_assets_by_key:
            raw_metadata = self.source_assets_by_key[asset_key].raw_metadata
            return raw_metadata or None
        elif asset_key in self.assets_defs_by_key:
            return self.assets_defs_by_key[asset_key].metadata_by_key[asset_key]
        else:
            check.failed(f"Couldn't find key {asset_key}")

    def asset_info_for_output(
        self, node_handle: NodeHandle, output_name: str
    ) -> Optional[AssetOutputInfo]:
        return self.asset_info_by_node_output_handle.get(NodeOutputHandle(node_handle, output_name))

    def asset_check_key_for_output(
        self, node_handle: NodeHandle, output_name: str
    ) -> Optional[AssetCheckKey]:
        return self.check_key_by_node_output_handle.get(NodeOutputHandle(node_handle, output_name))

    def group_names_by_assets(self) -> Mapping[AssetKey, str]:
        group_names: Dict[AssetKey, str] = {
            key: assets_def.group_names_by_key[key]
            for key, assets_def in self.assets_defs_by_key.items()
            if key in assets_def.group_names_by_key
        }

        group_names.update(
            {
                key: source_asset_def.group_name
                for key, source_asset_def in self.source_assets_by_key.items()
            }
        )

        return group_names

    def partitions_def_for_asset(self, asset_key: AssetKey) -> Optional["PartitionsDefinition"]:
        assets_def = self.assets_defs_by_key.get(asset_key)

        if assets_def is not None:
            return assets_def.partitions_def
        else:
            source_asset = self.source_assets_by_key.get(asset_key)
            if source_asset is not None:
                return source_asset.partitions_def

        return None

    def partition_mapping_for_node_input(
        self, node_handle: NodeHandle, upstream_asset_key: AssetKey
    ) -> Optional["PartitionMapping"]:
        return self.partition_mappings_by_asset_dep.get((node_handle.root, upstream_asset_key))

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
        return self.dep_asset_keys_by_node_output_handle.get(
            NodeOutputHandle(node_handle, output_name), set()
        )


def build_asset_selection_job(
    name: str,
    assets: Iterable["AssetsDefinition"],
    source_assets: Iterable["SourceAsset"],
    asset_checks: Iterable["AssetChecksDefinition"],
    executor_def: Optional[ExecutorDefinition] = None,
    config: Optional[Union[ConfigMapping, Mapping[str, Any], "PartitionedConfig"]] = None,
    partitions_def: Optional["PartitionsDefinition"] = None,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    description: Optional[str] = None,
    tags: Optional[Mapping[str, Any]] = None,
    metadata: Optional[Mapping[str, RawMetadataValue]] = None,
    asset_selection: Optional[AbstractSet[AssetKey]] = None,
    asset_check_selection: Optional[AbstractSet[AssetCheckKey]] = None,
    asset_selection_data: Optional[AssetSelectionData] = None,
    hooks: Optional[AbstractSet[HookDefinition]] = None,
) -> "JobDefinition":
    from dagster._core.definitions.assets_job import (
        build_assets_job,
        build_source_asset_observation_job,
    )

    if asset_selection is None and asset_check_selection is None:
        # no selections, include everything
        included_assets = list(assets)
        excluded_assets = []
        included_source_assets = list(source_assets)
        included_checks_defs = list(asset_checks)
    else:
        # Filter to assets that match either selected assets or include a selected check.
        # E.g. a multi asset can be included even if it's not in asset_selection, if it has a selected check
        # defined with check_specs
        (included_assets, excluded_assets) = _subset_assets_defs(
            assets, asset_selection or set(), asset_check_selection
        )
        included_source_assets = _subset_source_assets(source_assets, asset_selection or set())

        if asset_check_selection is None:
            # If assets were selected and checks are None, then include all checks on the selected assets.
            # Note: once we start explicitly passing in asset checks instead of None from the front end,
            # we can remove this logic.
            included_checks_defs = [
                asset_check
                for asset_check in asset_checks
                if asset_check.asset_key in check.not_none(asset_selection)
            ]
        else:
            # Otherwise, filter to explicitly selected checks defs
            included_checks_defs = [
                asset_check
                for asset_check in asset_checks
                if [spec for spec in asset_check.specs if spec.key in asset_check_selection]
            ]

    if partitions_def:
        for asset in included_assets:
            check.invariant(
                asset.partitions_def == partitions_def or asset.partitions_def is None,
                f"Assets defined for node '{asset.node_def.name}' have a partitions_def of "
                f"{asset.partitions_def}, but job '{name}' has non-matching partitions_def of "
                f"{partitions_def}.",
            )

    if len(included_assets) or len(included_checks_defs) > 0:
        asset_job = build_assets_job(
            name=name,
            assets=included_assets,
            asset_checks=included_checks_defs,
            config=config,
            source_assets=[*source_assets, *excluded_assets],
            resource_defs=resource_defs,
            executor_def=executor_def,
            partitions_def=partitions_def,
            description=description,
            tags=tags,
            metadata=metadata,
            hooks=hooks,
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
            hooks=hooks,
            _asset_selection_data=asset_selection_data,
        )

    return asset_job


def _subset_assets_defs(
    assets: Iterable["AssetsDefinition"],
    selected_asset_keys: AbstractSet[AssetKey],
    selected_asset_check_keys: Optional[AbstractSet[AssetCheckKey]],
) -> Tuple[Sequence["AssetsDefinition"], Sequence["AssetsDefinition"],]:
    """Given a list of asset key selection queries, generate a set of AssetsDefinition objects
    representing the included/excluded definitions.
    """
    included_assets: Set[AssetsDefinition] = set()
    excluded_assets: Set[AssetsDefinition] = set()

    for asset in set(assets):
        # intersection
        selected_subset = selected_asset_keys & asset.keys

        # if specific checks were selected, only include those
        if selected_asset_check_keys is not None:
            selected_check_subset = selected_asset_check_keys & asset.check_keys
        # if no checks were selected, filter to checks that target selected assets
        else:
            selected_check_subset = {
                handle for handle in asset.check_keys if handle.asset_key in selected_subset
            }

        # all assets in this def are selected
        if selected_subset == asset.keys and selected_check_subset == asset.check_keys:
            included_assets.add(asset)
        # no assets in this def are selected
        elif len(selected_subset) == 0 and len(selected_check_subset) == 0:
            excluded_assets.add(asset)
        elif asset.can_subset:
            # subset of the asset that we want
            subset_asset = asset.subset_for(selected_asset_keys, selected_check_subset)
            included_assets.add(subset_asset)
            # subset of the asset that we don't want
            excluded_assets.add(
                asset.subset_for(
                    selected_asset_keys=asset.keys - subset_asset.keys,
                    selected_asset_check_keys=(asset.check_keys - subset_asset.check_keys),
                )
            )
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
