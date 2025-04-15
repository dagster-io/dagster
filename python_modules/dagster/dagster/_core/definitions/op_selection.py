import itertools
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, AbstractSet, NamedTuple, Optional, Union, cast  # noqa: UP035

from dagster import _check as check
from dagster._core.definitions.dependency import (
    DependencyDefinition,
    DynamicCollectDependencyDefinition,
    GraphNode,
    IDependencyDefinition,
    MultiDependencyDefinition,
    NodeHandle,
    NodeInvocation,
    NodeOutput,
)
from dagster._core.definitions.graph_definition import GraphDefinition, SubselectedGraphDefinition
from dagster._core.errors import DagsterInvalidSubsetError
from dagster._core.selector.subset_selector import parse_op_queries

if TYPE_CHECKING:
    from dagster._core.definitions.composition import MappedInputPlaceholder
    from dagster._core.definitions.node_definition import NodeDefinition


class OpSelection:
    def __init__(self, query: Iterable[str]):
        self.query = query

    def resolve(self, graph_def: GraphDefinition) -> AbstractSet[str]:
        if any(["." in item for item in self.query]):
            resolved_node_paths = set(self.query)
            _validate_node_paths(resolved_node_paths, graph_def)
        else:
            # validation happens inside parse_op_queries
            resolved_node_paths = set(parse_op_queries(graph_def, list(self.query)))
        return resolved_node_paths


class OpSelectionNode(NamedTuple):
    name: str
    children: list["OpSelectionNode"]

    @property
    def is_leaf(self) -> bool:
        return not self.children

    def has_child(self, name: str) -> bool:
        return any(child.name == name for child in self.children)

    def get_child(self, name: str) -> "OpSelectionNode":
        return next(child for child in self.children if child.name == name)


def _validate_node_paths(node_paths: Iterable[str], graph_def: GraphDefinition) -> None:
    selection_tree = _node_paths_to_tree(node_paths)
    _validate_selection_tree(selection_tree, graph_def)


def _node_paths_to_tree(node_paths: Iterable[str]) -> OpSelectionNode:
    node_path_lists = sorted([tuple(path.split(".")) for path in node_paths])
    return _node_path_lists_to_tree(node_path_lists)


def _node_path_lists_to_tree(paths: Sequence[tuple[str, ...]]) -> OpSelectionNode:
    root = OpSelectionNode("ROOT", [])
    for k, group in itertools.groupby(paths, lambda x: x[0]):
        child = _node_path_lists_to_tree([x[1:] for x in group if len(x) > 1])._replace(name=k)
        root.children.append(child)
    return root


def _validate_selection_tree(selection_tree: OpSelectionNode, graph_def: GraphDefinition) -> None:
    for selection_child in selection_tree.children:
        node_name = selection_child.name
        if not graph_def.has_node_named(node_name):
            raise DagsterInvalidSubsetError(
                f"Node {node_name} was selected, but no node named {node_name} was found."
            )
        if not selection_child.is_leaf:
            graph_child = graph_def.node_named(node_name)
            if isinstance(graph_child, GraphNode):
                _validate_selection_tree(selection_child, graph_child.definition)
            else:
                raise DagsterInvalidSubsetError(
                    f"Children of node {node_name} were selected, but {node_name} is not a graph."
                )


def get_graph_subset(
    graph: GraphDefinition,
    op_selection: Iterable[str],
    selected_outputs_by_op_handle: Mapping[NodeHandle, AbstractSet[str]],
) -> SubselectedGraphDefinition:
    """Returns a subsetted version of the given graph.

    Args:
        selected_outputs_by_op_handle: A mapping of op handles to the set of output names that are
            selected within that op. If an op handle isn't included in this dict, it means that
            _all_ its outputs are selected.
    """
    node_paths = OpSelection(op_selection).resolve(graph)
    selection_tree = _node_paths_to_tree(node_paths)
    return _get_graph_subset(
        graph,
        selection_tree,
        parent_handle=None,
        selected_outputs_by_op_handle=selected_outputs_by_op_handle,
    )


def _get_graph_subset(
    graph: GraphDefinition,
    selection_tree: OpSelectionNode,
    parent_handle: Optional[NodeHandle],
    selected_outputs_by_op_handle: Mapping[NodeHandle, AbstractSet[str]],
) -> SubselectedGraphDefinition:
    subgraph_deps: dict[
        NodeInvocation,
        dict[str, IDependencyDefinition],
    ] = {}

    subgraph_nodes: dict[str, NodeDefinition] = {}

    for node in graph.nodes_in_topological_order:
        # skip if the node isn't selected
        if not selection_tree.has_child(node.name):
            continue

        node_handle = NodeHandle(node.name, parent=parent_handle)
        node_def: Union[SubselectedGraphDefinition, NodeDefinition] = node.definition
        node_selection_tree = selection_tree.get_child(node.name)

        # subselect graph if any nodes inside the graph are selected
        if isinstance(node, GraphNode) and not node_selection_tree.is_leaf:
            node_def = _get_graph_subset(
                node.definition,
                node_selection_tree,
                parent_handle=node_handle,
                selected_outputs_by_op_handle=selected_outputs_by_op_handle,
            )

        subgraph_nodes[node.name] = node_def

        def is_output_selected(node_output: NodeOutput) -> bool:
            if not selection_tree.has_child(node_output.node_name):
                return False

            output_def, op_handle = graph.node_named(
                node_output.node_name
            ).definition.resolve_output_to_origin(
                node_output.output_name, NodeHandle(node_output.node_name, parent_handle)
            )
            return (
                op_handle not in selected_outputs_by_op_handle
                or output_def.name in selected_outputs_by_op_handle[check.not_none(op_handle)]
            )

        # build dependencies for the node. we do it for both cases because nested graphs can have
        # inputs and outputs too
        node_deps: dict[str, IDependencyDefinition] = {}
        for node_input in node.inputs():
            if graph.dependency_structure.has_direct_dep(node_input):
                node_output = graph.dependency_structure.get_direct_dep(node_input)
                if is_output_selected(node_output):
                    node_deps[node_input.input_name] = DependencyDefinition(
                        node=node_output.node.name, output=node_output.output_name
                    )
            elif graph.dependency_structure.has_dynamic_fan_in_dep(node_input):
                node_output = graph.dependency_structure.get_dynamic_fan_in_dep(node_input)
                if is_output_selected(node_output):
                    node_deps[node_input.input_name] = DynamicCollectDependencyDefinition(
                        node_name=node_output.node_name,
                        output_name=node_output.output_name,
                    )
            elif graph.dependency_structure.has_fan_in_deps(node_input):
                outputs = graph.dependency_structure.get_fan_in_deps(node_input)
                multi_dependencies = [
                    DependencyDefinition(
                        node=output_handle.node.name, output=output_handle.output_def.name
                    )
                    for output_handle in outputs
                    if (isinstance(output_handle, NodeOutput) and is_output_selected(output_handle))
                ]
                node_deps[node_input.input_name] = MultiDependencyDefinition(
                    cast(
                        "list[Union[DependencyDefinition, type[MappedInputPlaceholder]]]",
                        multi_dependencies,
                    )
                )
            # else input is unconnected

        dep_key = NodeInvocation(
            name=node.definition.name,
            alias=node.name,
            tags=node.tags,
            hook_defs=node.hook_defs,
            retry_policy=node.retry_policy,
        )
        subgraph_deps[dep_key] = node_deps

    # filter out unselected input/output mapping
    subgraph_input_mappings = [
        imap for imap in graph.input_mappings if imap.maps_to.node_name in subgraph_nodes.keys()
    ]
    subgraph_output_mappings = [
        omap for omap in graph.output_mappings if omap.maps_from.node_name in subgraph_nodes.keys()
    ]

    return SubselectedGraphDefinition(
        parent_graph_def=graph,
        dependencies=subgraph_deps,
        node_defs=list(subgraph_nodes.values()),
        input_mappings=subgraph_input_mappings,
        output_mappings=subgraph_output_mappings,
    )
