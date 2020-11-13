from abc import ABCMeta, abstractmethod, abstractproperty
from collections import defaultdict

import six
from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.types.dagster_type import DagsterTypeKind

from .dependency import DependencyStructure, IDependencyDefinition, Solid, SolidInvocation


class IContainSolids(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractproperty
    def solids(self):
        """List[Solid]: Top-level solids in the container."""

    @abstractproperty
    def dependency_structure(self):
        """DependencyStructure: The dependencies between top-level solids in the container."""

    @abstractmethod
    def solid_named(self, name):
        """Return the (top-level) solid with a given name.

        Args:
            name (str): The name of the top level solid.

        Returns:
            Solid: The solid with the given name
        """


def validate_dependency_dict(dependencies):
    prelude = (
        'The expected type for "dependencies" is dict[Union[str, SolidInvocation], dict[str, '
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
        if not (isinstance(key, str) or isinstance(key, SolidInvocation)):
            raise DagsterInvalidDefinitionError(
                prelude + "Expected str or SolidInvocation key in the top level dict. "
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
                    prelude
                    + "Received non-sting key in the inner dict for key {key}.".format(key=key)
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


def create_execution_structure(solid_defs, dependencies_dict, graph_definition):
    """This builder takes the dependencies dictionary specified during creation of the
    PipelineDefinition object and builds (1) the execution structure and (2) a solid dependency
    dictionary.

    For example, for the following dependencies:

    dep_dict = {
            SolidInvocation('giver'): {},
            SolidInvocation('sleeper', alias='sleeper_1'): {
                'units': DependencyDefinition('giver', 'out_1')
            },
            SolidInvocation('sleeper', alias='sleeper_2'): {
                'units': DependencyDefinition('giver', 'out_2')
            },
            SolidInvocation('sleeper', alias='sleeper_3'): {
                'units': DependencyDefinition('giver', 'out_3')
            },
            SolidInvocation('sleeper', alias='sleeper_4'): {
                'units': DependencyDefinition('giver', 'out_4')
            },
            SolidInvocation('total'): {
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
    from .solid import NodeDefinition
    from .graph import GraphDefinition

    check.list_param(solid_defs, "solid_defs", of_type=NodeDefinition)
    check.dict_param(
        dependencies_dict, "dependencies_dict", key_type=(str, SolidInvocation), value_type=dict,
    )
    # graph_definition is none in the context of a pipeline
    check.inst_param(graph_definition, "graph_definition", GraphDefinition)

    # Same as dep_dict but with SolidInvocation replaced by alias string
    aliased_dependencies_dict = {}

    # Keep track of solid name -> all aliases used and alias -> name
    name_to_aliases = defaultdict(set)
    alias_to_solid_instance = {}
    alias_to_name = {}

    for solid_key, input_dep_dict in dependencies_dict.items():
        # We allow deps of the form dependencies={'foo': DependencyDefinition('bar')}
        # Here, we replace 'foo' with SolidInvocation('foo')
        if not isinstance(solid_key, SolidInvocation):
            solid_key = SolidInvocation(solid_key)

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
    solid_defs, name_to_aliases, alias_to_solid_instance, graph_definition
):
    pipeline_solids = []
    for solid_def in solid_defs:
        uses_of_solid = name_to_aliases.get(solid_def.name, {solid_def.name})

        for alias in uses_of_solid:
            solid_instance = alias_to_solid_instance.get(alias)

            solid_instance_tags = solid_instance.tags if solid_instance else {}
            hook_defs = solid_instance.hook_defs if solid_instance else frozenset()
            pipeline_solids.append(
                Solid(
                    name=alias,
                    definition=solid_def,
                    graph_definition=graph_definition,
                    tags=solid_instance_tags,
                    hook_defs=hook_defs,
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
                            "Invalid dependencies: circular reference detected in solid "
                            '"{from_solid}" input "{from_input}"'
                        ).format(from_solid=from_solid, from_input=from_input)
                    )

                if not from_solid in solid_dict:
                    aliased_solid = alias_to_name.get(from_solid)
                    if aliased_solid == from_solid:
                        raise DagsterInvalidDefinitionError(
                            'Invalid dependencies: solid "{solid}" in dependency dictionary not '
                            "found in solid list".format(solid=from_solid)
                        )
                    else:
                        raise DagsterInvalidDefinitionError(
                            (
                                'Invalid dependencies: solid "{aliased_solid}" (aliased by '
                                '"{from_solid}" in dependency dictionary) not found in solid list'
                            ).format(aliased_solid=aliased_solid, from_solid=from_solid)
                        )
                if not solid_dict[from_solid].definition.has_input(from_input):
                    input_list = solid_dict[from_solid].definition.input_dict.keys()
                    raise DagsterInvalidDefinitionError(
                        'Invalid dependencies: solid "{from_solid}" does not have input '
                        '"{from_input}". '.format(from_solid=from_solid, from_input=from_input)
                        + "Available inputs: {input_list}".format(input_list=input_list)
                    )

                if not dep.solid in solid_dict:
                    raise DagsterInvalidDefinitionError(
                        'Invalid dependencies: solid "{dep.solid}" not found in solid list. '
                        'Listed as dependency for solid "{from_solid}" input "{from_input}" '.format(
                            dep=dep, from_solid=from_solid, from_input=from_input
                        )
                    )

                if not solid_dict[dep.solid].definition.has_output(dep.output):
                    raise DagsterInvalidDefinitionError(
                        'Invalid dependencies: solid "{dep.solid}" does not have output '
                        '"{dep.output}". Listed as dependency for solid "{from_solid} input '
                        '"{from_input}"'.format(
                            dep=dep, from_solid=from_solid, from_input=from_input
                        )
                    )

                input_def = solid_dict[from_solid].definition.input_def_named(from_input)
                output_def = solid_dict[dep.solid].definition.output_def_named(dep.output)

                if dep_def.is_multi() and not input_def.dagster_type.supports_fan_in:
                    raise DagsterInvalidDefinitionError(
                        f'Invalid dependencies: for solid "{dep.solid}" input "{input_def.name}", the '
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
                'Input "{input_def.name}" to solid "{from_solid}" can not depend on the output '
                '"{output_def.name}" from solid "{dep.solid}". '
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
