from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Optional, TypeVar, Union

import dagster._check as check
from dagster._core.definitions.dependency import (
    DependencyMapping,
    DependencyStructure,
    GraphNode,
    IDependencyDefinition,
    Node,
    NodeInvocation,
    OpNode,
)
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.errors import DagsterInvalidDefinitionError

if TYPE_CHECKING:
    from dagster._core.definitions.graph_definition import GraphDefinition
    from dagster._core.definitions.node_definition import NodeDefinition

T_DependencyKey = TypeVar("T_DependencyKey", str, "NodeInvocation")


def normalize_dependency_dict(
    dependencies: Optional[Union[DependencyMapping[str], DependencyMapping[NodeInvocation]]],
) -> DependencyMapping[NodeInvocation]:
    prelude = (
        'The expected type for "dependencies" is Union[Mapping[str, Mapping[str, '
        "DependencyDefinition]], Mapping[NodeInvocation, Mapping[str, DependencyDefinition]]]. "
    )

    if dependencies is None:
        return {}

    if not isinstance(dependencies, dict):
        raise DagsterInvalidDefinitionError(
            prelude + "Received value {dependencies} of type {type(dependencies)} at the top level."
        )

    normalized_dependencies: dict[NodeInvocation, Mapping[str, IDependencyDefinition]] = {}
    for key, dep_dict in dependencies.items():
        if not isinstance(dep_dict, dict):
            if isinstance(dep_dict, IDependencyDefinition):
                raise DagsterInvalidDefinitionError(
                    prelude
                    + f"Received a IDependencyDefinition one layer too high under key {key}. "
                    "The DependencyDefinition should be moved in to a dict keyed on "
                    "input name."
                )
            else:
                raise DagsterInvalidDefinitionError(
                    prelude
                    + f"Under key {key} received value {dep_dict} of type {type(dep_dict)}. "
                    "Expected dict[str, DependencyDefinition]"
                )

        for input_key, dep in dep_dict.items():
            if not isinstance(input_key, str):
                raise DagsterInvalidDefinitionError(
                    prelude + f"Received non-string key in the inner dict for key {key}. "
                    f"Unexpected inner dict key type: {type(input_key)}"
                )
            if not isinstance(dep, IDependencyDefinition):
                raise DagsterInvalidDefinitionError(
                    prelude
                    + f'Expected IDependencyDefinition for node "{key}" input "{input_key}". '
                    f"Received value {dep} of type {type(dep)}."
                )

        if isinstance(key, str):
            normalized_dependencies[NodeInvocation(key)] = dep_dict
        elif isinstance(key, NodeInvocation):
            normalized_dependencies[key] = dep_dict
        else:
            raise DagsterInvalidDefinitionError(
                prelude + "Expected str or NodeInvocation key in the top level dict. "
                "Received value {key} of type {type(key)}"
            )

    return normalized_dependencies


def create_execution_structure(
    node_defs: Sequence["NodeDefinition"],
    dependencies_dict: DependencyMapping[NodeInvocation],
    graph_definition: "GraphDefinition",
) -> tuple[DependencyStructure, Mapping[str, Node]]:
    """This builder takes the dependencies dictionary specified during creation of the
    JobDefinition object and builds (1) the execution structure and (2) a node dependency
    dictionary.

    For example, for the following dependencies:

    dep_dict = {
            NodeInvocation('giver'): {},
            NodeInvocation('sleeper', alias='sleeper_1'): {
                'units': DependencyDefinition('giver', 'out_1')
            },
            NodeInvocation('sleeper', alias='sleeper_2'): {
                'units': DependencyDefinition('giver', 'out_2')
            },
            NodeInvocation('sleeper', alias='sleeper_3'): {
                'units': DependencyDefinition('giver', 'out_3')
            },
            NodeInvocation('sleeper', alias='sleeper_4'): {
                'units': DependencyDefinition('giver', 'out_4')
            },
            NodeInvocation('total'): {
                'in_1': DependencyDefinition('sleeper_1', 'total'),
                'in_2': DependencyDefinition('sleeper_2', 'total'),
                'in_3': DependencyDefinition('sleeper_3', 'total'),
                'in_4': DependencyDefinition('sleeper_4', 'total'),
            },
        },

    This will create:

    node_dict = {
        'giver': <dagster._core.definitions.dependency.Node object>,
        'sleeper_1': <dagster._core.definitions.dependency.Node object>,
        'sleeper_2': <dagster._core.definitions.dependency.Node object>,
        'sleeper_3': <dagster._core.definitions.dependency.Node object>,
        'sleeper_4': <dagster._core.definitions.dependency.Node object>,
        'total': <dagster._core.definitions.dependency.Node object>
    }

    as well as a dagster._core.definitions.dependency.DependencyStructure object.
    """
    from dagster._core.definitions.graph_definition import GraphDefinition
    from dagster._core.definitions.node_definition import NodeDefinition

    check.sequence_param(node_defs, "node_defs", of_type=NodeDefinition)
    check.mapping_param(
        dependencies_dict,
        "dependencies_dict",
        key_type=(str, NodeInvocation),
        value_type=dict,
    )
    check.inst_param(graph_definition, "graph_definition", GraphDefinition)

    # Same as dep_dict but with NodeInvocation replaced by alias string
    aliased_dependencies_dict: dict[str, Mapping[str, IDependencyDefinition]] = {}

    # Keep track of node name -> all aliases used and alias -> name
    name_to_aliases: defaultdict[str, set[str]] = defaultdict(set)
    alias_to_node_invocation: dict[str, NodeInvocation] = {}
    alias_to_name: dict[str, str] = {}

    for node_invocation, input_dep_dict in dependencies_dict.items():
        # We allow deps of the form dependencies={'foo': DependencyDefinition('bar')}
        # Here, we replace 'foo' with NodeInvocation('foo')

        alias = node_invocation.alias or node_invocation.name

        name_to_aliases[node_invocation.name].add(alias)
        alias_to_node_invocation[alias] = node_invocation
        alias_to_name[alias] = node_invocation.name
        aliased_dependencies_dict[alias] = input_dep_dict

    node_dict = _build_graph_node_dict(
        node_defs, name_to_aliases, alias_to_node_invocation, graph_definition
    )

    _validate_dependencies(aliased_dependencies_dict, node_dict, alias_to_name)

    dependency_structure = DependencyStructure.from_definitions(
        node_dict, aliased_dependencies_dict
    )

    return dependency_structure, node_dict


def _build_graph_node_dict(
    node_defs: Sequence["NodeDefinition"],
    name_to_aliases: Mapping[str, set[str]],
    alias_to_node_invocation: Mapping[str, NodeInvocation],
    graph_definition,
) -> Mapping[str, Node]:
    from dagster._core.definitions.graph_definition import GraphDefinition

    nodes: list[Node] = []
    for node_def in node_defs:
        uses_of_node = name_to_aliases.get(node_def.name, {node_def.name})

        for alias in uses_of_node:
            node_invocation = alias_to_node_invocation.get(alias)

            node_invocation_tags = node_invocation.tags if node_invocation else {}
            hook_defs = node_invocation.hook_defs if node_invocation else frozenset()
            retry_policy = node_invocation.retry_policy if node_invocation else None
            node: Node
            if isinstance(node_def, GraphDefinition):
                node = GraphNode(
                    name=alias,
                    definition=node_def,
                    graph_definition=graph_definition,
                    tags=node_invocation_tags,
                    hook_defs=hook_defs,
                    retry_policy=retry_policy,
                )
            elif isinstance(node_def, OpDefinition):
                node = OpNode(
                    name=alias,
                    definition=node_def,
                    graph_definition=graph_definition,
                    tags=node_invocation_tags,
                    hook_defs=hook_defs,
                    retry_policy=retry_policy,
                )
            else:
                check.failed(f"Unexpected node_def type {node_def}")
            nodes.append(node)

    return {node.name: node for node in nodes}


def _validate_dependencies(
    dependencies: DependencyMapping[str],
    node_dict: Mapping[str, Node],
    alias_to_name: Mapping[str, str],
) -> None:
    for from_node, dep_by_input in dependencies.items():
        for from_input, dep_def in dep_by_input.items():
            for dep in dep_def.get_node_dependencies():
                if from_node == dep.node:
                    raise DagsterInvalidDefinitionError(
                        "Invalid dependencies: circular reference detected in node "
                        f'"{from_node}" input "{from_input}"'
                    )

                if from_node not in node_dict:
                    aliased_node = alias_to_name.get(from_node)
                    if aliased_node == from_node:
                        raise DagsterInvalidDefinitionError(
                            f'Invalid dependencies: node "{from_node}" in dependency dictionary not'
                            " found in node list"
                        )
                    else:
                        raise DagsterInvalidDefinitionError(
                            f'Invalid dependencies: node "{aliased_node}" (aliased by '
                            f'"{from_node}" in dependency dictionary) not found in node list'
                        )
                if not node_dict[from_node].definition.has_input(from_input):
                    from dagster._core.definitions.graph_definition import GraphDefinition

                    input_list = node_dict[from_node].definition.input_dict.keys()
                    node_type = (
                        "graph"
                        if isinstance(node_dict[from_node].definition, GraphDefinition)
                        else "op"
                    )
                    raise DagsterInvalidDefinitionError(
                        f'Invalid dependencies: {node_type} "{from_node}" does not have input '
                        f'"{from_input}". Available inputs: {list(input_list)}'
                    )

                if dep.node not in node_dict:
                    raise DagsterInvalidDefinitionError(
                        f'Invalid dependencies: node "{dep.node}" not found in node list. '
                        f'Listed as dependency for node "{from_node}" input "{from_input}" '
                    )

                if not node_dict[dep.node].definition.has_output(dep.output):
                    raise DagsterInvalidDefinitionError(
                        f'Invalid dependencies: node "{dep.node}" does not have output '
                        f'"{dep.output}". Listed as dependency for node "{from_node} input '
                        f'"{from_input}"'
                    )

                input_def = node_dict[from_node].definition.input_def_named(from_input)

                if dep_def.is_fan_in() and not input_def.dagster_type.supports_fan_in:
                    raise DagsterInvalidDefinitionError(
                        f'Invalid dependencies: for node "{dep.node}" input "{input_def.name}", the'
                        f' DagsterType "{input_def.dagster_type.display_name}" does not support'
                        " fanning in (MultiDependencyDefinition). Use the List type, since fanning"
                        " in will result in a list."
                    )
