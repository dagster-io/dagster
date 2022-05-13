from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple, Union

import dagster._check as check
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.types.dagster_type import DagsterTypeKind

from .dependency import DependencyStructure, IDependencyDefinition, Node, NodeInvocation

if TYPE_CHECKING:
    from .graph_definition import GraphDefinition
    from .solid_definition import NodeDefinition


def validate_dependency_dict(
    dependencies: Optional[Dict[Union[str, NodeInvocation], Dict[str, IDependencyDefinition]]],
) -> Dict[Union[str, NodeInvocation], Dict[str, IDependencyDefinition]]:
    prelude = (
        'The expected type for "dependencies" is Dict[Union[str, NodeInvocation], Dict[str, '
        "DependencyDefinition]]. "
    )

    if dependencies is None:
        return {}

    if not isinstance(dependencies, dict):
        raise DagsterInvalidDefinitionError(
            prelude
            + "Received value {val} of type {type} at the top level.".format(
                val=dependencies, type=type(dependencies)
            )
        )

    for key, dep_dict in dependencies.items():
        if not (isinstance(key, str) or isinstance(key, NodeInvocation)):
            raise DagsterInvalidDefinitionError(
                prelude + "Expected str or NodeInvocation key in the top level dict. "
                "Received value {val} of type {type}".format(val=key, type=type(key))
            )
        if not isinstance(dep_dict, dict):
            if isinstance(dep_dict, IDependencyDefinition):
                raise DagsterInvalidDefinitionError(
                    prelude
                    + "Received a IDependencyDefinition one layer too high under key {key}. "
                    "The DependencyDefinition should be moved in to a dict keyed on "
                    "input name.".format(key=key)
                )
            else:
                raise DagsterInvalidDefinitionError(
                    prelude + "Under key {key} received value {val} of type {type}. "
                    "Expected dict[str, DependencyDefinition]".format(
                        key=key, val=dep_dict, type=type(dep_dict)
                    )
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
                    + 'Expected IDependencyDefinition for solid "{key}" input "{input_key}". '
                    "Received value {val} of type {type}.".format(
                        key=key, input_key=input_key, val=dep, type=type(dep)
                    )
                )

    return dependencies


def create_execution_structure(
    solid_defs: List["NodeDefinition"],
    dependencies_dict: Dict[Union[str, NodeInvocation], Dict[str, IDependencyDefinition]],
    graph_definition: "GraphDefinition",
) -> Tuple[DependencyStructure, Dict[str, Node]]:
    """This builder takes the dependencies dictionary specified during creation of the
    PipelineDefinition object and builds (1) the execution structure and (2) a solid dependency
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

    pipeline_solid_dict = {
        'giver': <dagster.core.definitions.dependency.Solid object>,
        'sleeper_1': <dagster.core.definitions.dependency.Solid object>,
        'sleeper_2': <dagster.core.definitions.dependency.Solid object>,
        'sleeper_3': <dagster.core.definitions.dependency.Solid object>,
        'sleeper_4': <dagster.core.definitions.dependency.Solid object>,
        'total': <dagster.core.definitions.dependency.Solid object>
    }

    as well as a dagster.core.definitions.dependency.DependencyStructure object.
    """
    from .graph_definition import GraphDefinition
    from .solid_definition import NodeDefinition

    check.list_param(solid_defs, "solid_defs", of_type=NodeDefinition)
    check.dict_param(
        dependencies_dict,
        "dependencies_dict",
        key_type=(str, NodeInvocation),
        value_type=dict,
    )
    # graph_definition is none in the context of a pipeline
    check.inst_param(graph_definition, "graph_definition", GraphDefinition)

    # Same as dep_dict but with NodeInvocation replaced by alias string
    aliased_dependencies_dict = {}

    # Keep track of solid name -> all aliases used and alias -> name
    name_to_aliases = defaultdict(set)
    alias_to_solid_instance = {}
    alias_to_name = {}

    for solid_key, input_dep_dict in dependencies_dict.items():
        # We allow deps of the form dependencies={'foo': DependencyDefinition('bar')}
        # Here, we replace 'foo' with NodeInvocation('foo')
        if not isinstance(solid_key, NodeInvocation):
            solid_key = NodeInvocation(solid_key)

        alias = solid_key.alias or solid_key.name

        name_to_aliases[solid_key.name].add(alias)
        alias_to_solid_instance[alias] = solid_key
        alias_to_name[alias] = solid_key.name
        aliased_dependencies_dict[alias] = input_dep_dict

    pipeline_solid_dict = _build_pipeline_solid_dict(
        solid_defs, name_to_aliases, alias_to_solid_instance, graph_definition
    )

    _validate_dependencies(aliased_dependencies_dict, pipeline_solid_dict, alias_to_name)

    dependency_structure = DependencyStructure.from_definitions(
        pipeline_solid_dict, aliased_dependencies_dict
    )

    return dependency_structure, pipeline_solid_dict


def _build_pipeline_solid_dict(
    solid_defs: List["NodeDefinition"],
    name_to_aliases: Dict[str, Set[str]],
    alias_to_solid_instance: Dict[str, NodeInvocation],
    graph_definition,
) -> Dict[str, Node]:
    pipeline_solids = []
    for solid_def in solid_defs:
        uses_of_solid = name_to_aliases.get(solid_def.name, {solid_def.name})

        for alias in uses_of_solid:
            solid_instance = alias_to_solid_instance.get(alias)

            solid_instance_tags = solid_instance.tags if solid_instance else {}
            hook_defs = solid_instance.hook_defs if solid_instance else frozenset()
            retry_policy = solid_instance.retry_policy if solid_instance else None
            pipeline_solids.append(
                Node(
                    name=alias,
                    definition=solid_def,
                    graph_definition=graph_definition,
                    tags=solid_instance_tags,
                    hook_defs=hook_defs,
                    retry_policy=retry_policy,
                )
            )

    return {ps.name: ps for ps in pipeline_solids}


def _validate_dependencies(dependencies, solid_dict, alias_to_name):
    for from_solid, dep_by_input in dependencies.items():
        for from_input, dep_def in dep_by_input.items():
            for dep in dep_def.get_solid_dependencies():

                if from_solid == dep.solid:
                    raise DagsterInvalidDefinitionError(
                        (
                            "Invalid dependencies: circular reference detected in node "
                            '"{from_solid}" input "{from_input}"'
                        ).format(from_solid=from_solid, from_input=from_input)
                    )

                if not from_solid in solid_dict:
                    aliased_solid = alias_to_name.get(from_solid)
                    if aliased_solid == from_solid:
                        raise DagsterInvalidDefinitionError(
                            'Invalid dependencies: node "{solid}" in dependency dictionary not '
                            "found in node list".format(solid=from_solid)
                        )
                    else:
                        raise DagsterInvalidDefinitionError(
                            (
                                'Invalid dependencies: node "{aliased_solid}" (aliased by '
                                '"{from_solid}" in dependency dictionary) not found in node list'
                            ).format(aliased_solid=aliased_solid, from_solid=from_solid)
                        )
                if not solid_dict[from_solid].definition.has_input(from_input):
                    from .graph_definition import GraphDefinition

                    input_list = solid_dict[from_solid].definition.input_dict.keys()
                    node_type = (
                        "graph"
                        if isinstance(solid_dict[from_solid].definition, GraphDefinition)
                        else "solid"
                    )
                    raise DagsterInvalidDefinitionError(
                        'Invalid dependencies: {node_type} "{from_solid}" does not have input '
                        '"{from_input}". '.format(
                            node_type=node_type, from_solid=from_solid, from_input=from_input
                        )
                        + "Available inputs: {input_list}".format(input_list=list(input_list))
                    )

                if not dep.solid in solid_dict:
                    raise DagsterInvalidDefinitionError(
                        'Invalid dependencies: node "{dep.solid}" not found in node list. '
                        'Listed as dependency for node "{from_solid}" input "{from_input}" '.format(
                            dep=dep, from_solid=from_solid, from_input=from_input
                        )
                    )

                if not solid_dict[dep.solid].definition.has_output(dep.output):
                    raise DagsterInvalidDefinitionError(
                        'Invalid dependencies: node "{dep.solid}" does not have output '
                        '"{dep.output}". Listed as dependency for node "{from_solid} input '
                        '"{from_input}"'.format(
                            dep=dep, from_solid=from_solid, from_input=from_input
                        )
                    )

                input_def = solid_dict[from_solid].definition.input_def_named(from_input)
                output_def = solid_dict[dep.solid].definition.output_def_named(dep.output)

                if dep_def.is_fan_in() and not input_def.dagster_type.supports_fan_in:
                    raise DagsterInvalidDefinitionError(
                        f'Invalid dependencies: for node "{dep.solid}" input "{input_def.name}", the '
                        f'DagsterType "{input_def.dagster_type.display_name}" does not support fanning in '
                        "(MultiDependencyDefinition). Use the List type, since fanning in will result in a list."
                    )

                _validate_input_output_pair(input_def, output_def, from_solid, dep)


def _validate_input_output_pair(input_def, output_def, from_solid, dep):
    # Currently, we opt to be overly permissive with input/output type mismatches.

    # Here we check for the case where no value will be provided where one is expected.
    if (
        output_def.dagster_type.kind == DagsterTypeKind.NOTHING
        and not input_def.dagster_type.kind == DagsterTypeKind.NOTHING
    ):
        raise DagsterInvalidDefinitionError(
            (
                'Input "{input_def.name}" to node "{from_solid}" can not depend on the output '
                '"{output_def.name}" from node "{dep.solid}". '
                'Input "{input_def.name}" expects a value of type '
                '{input_def.dagster_type.display_name} and output "{output_def.name}" returns '
                "type {output_def.dagster_type.display_name}{extra}."
            ).format(
                from_solid=from_solid,
                dep=dep,
                output_def=output_def,
                input_def=input_def,
                extra=" (which produces no value)"
                if output_def.dagster_type.kind == DagsterTypeKind.NOTHING
                else "",
            )
        )
