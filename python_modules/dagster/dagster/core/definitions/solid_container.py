from abc import ABCMeta, abstractmethod, abstractproperty
from collections import defaultdict

import six
from toposort import CircularDependencyError

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.types.dagster_type import DagsterTypeKind
from dagster.core.utils import toposort_flatten

from .dependency import DependencyStructure, IDependencyDefinition, Solid, SolidInvocation


class IContainSolids(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractproperty
    def solids(self):
        pass

    @abstractproperty
    def dependency_structure(self):
        pass

    @abstractmethod
    def solid_named(self, name):
        pass

    def _solids_in_topological_order(self):
        _forward_edges, backward_edges = _create_adjacency_lists(
            self.solids, self.dependency_structure
        )

        try:
            order = toposort_flatten(backward_edges)
        except CircularDependencyError as err:
            six.raise_from(
                DagsterInvalidDefinitionError(str(err)), err,
            )

        return [self.solid_named(solid_name) for solid_name in order]


def _create_adjacency_lists(solids, dep_structure):
    check.list_param(solids, 'solids', Solid)
    check.inst_param(dep_structure, 'dep_structure', DependencyStructure)

    visit_dict = {s.name: False for s in solids}
    forward_edges = {s.name: set() for s in solids}
    backward_edges = {s.name: set() for s in solids}

    def visit(solid_name):
        if visit_dict[solid_name]:
            return

        visit_dict[solid_name] = True

        for output_handle in dep_structure.all_upstream_outputs_from_solid(solid_name):
            forward_node = output_handle.solid.name
            backward_node = solid_name
            if forward_node in forward_edges:
                forward_edges[forward_node].add(backward_node)
                backward_edges[backward_node].add(forward_node)
                visit(forward_node)

    for s in solids:
        visit(s.name)

    return (forward_edges, backward_edges)


def validate_dependency_dict(dependencies):
    prelude = (
        'The expected type for "dependencies" is dict[Union[str, SolidInvocation], dict[str, '
        'DependencyDefinition]]. '
    )

    if dependencies is None:
        return {}

    if not isinstance(dependencies, dict):
        raise DagsterInvalidDefinitionError(
            prelude
            + 'Received value {val} of type {type} at the top level.'.format(
                val=dependencies, type=type(dependencies)
            )
        )

    for key, dep_dict in dependencies.items():
        if not (isinstance(key, six.string_types) or isinstance(key, SolidInvocation)):
            raise DagsterInvalidDefinitionError(
                prelude + 'Expected str or SolidInvocation key in the top level dict. '
                'Received value {val} of type {type}'.format(val=key, type=type(key))
            )
        if not isinstance(dep_dict, dict):
            if isinstance(dep_dict, IDependencyDefinition):
                raise DagsterInvalidDefinitionError(
                    prelude
                    + 'Received a IDependencyDefinition one layer too high under key {key}. '
                    'The DependencyDefinition should be moved in to a dict keyed on '
                    'input name.'.format(key=key)
                )
            else:
                raise DagsterInvalidDefinitionError(
                    prelude + 'Under key {key} received value {val} of type {type}. '
                    'Expected dict[str, DependencyDefinition]'.format(
                        key=key, val=dep_dict, type=type(dep_dict)
                    )
                )

        for input_key, dep in dep_dict.items():
            if not isinstance(input_key, six.string_types):
                raise DagsterInvalidDefinitionError(
                    prelude
                    + 'Received non-sting key in the inner dict for key {key}.'.format(key=key)
                )
            if not isinstance(dep, IDependencyDefinition):
                raise DagsterInvalidDefinitionError(
                    prelude
                    + 'Expected IDependencyDefinition for solid "{key}" input "{input_key}". '
                    'Received value {val} of type {type}.'.format(
                        key=key, input_key=input_key, val=dep, type=type(dep)
                    )
                )

    return dependencies


def create_execution_structure(solid_defs, dependencies_dict, container_definition):
    '''This builder takes the dependencies dictionary specified during creation of the
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
    '''
    from .solid import ISolidDefinition, CompositeSolidDefinition

    check.list_param(solid_defs, 'solid_defs', of_type=ISolidDefinition)
    check.dict_param(
        dependencies_dict,
        'dependencies_dict',
        key_type=six.string_types + (SolidInvocation,),
        value_type=dict,
    )
    # container_definition is none in the context of a pipeline
    check.opt_inst_param(container_definition, 'container_definition', CompositeSolidDefinition)

    # Same as dep_dict but with SolidInvocation replaced by alias string
    aliased_dependencies_dict = {}

    # Keep track of solid name -> all aliases used and alias -> name
    name_to_aliases = defaultdict(set)
    alias_to_solid_instance = {}
    alias_to_name = {}

    for solid_key, input_dep_dict in dependencies_dict.items():
        # We allow deps of the form dependencies={'foo': DependencyDefition('bar')}
        # Here, we replace 'foo' with SolidInvocation('foo')
        if not isinstance(solid_key, SolidInvocation):
            solid_key = SolidInvocation(solid_key)

        alias = solid_key.alias or solid_key.name

        name_to_aliases[solid_key.name].add(alias)
        alias_to_solid_instance[alias] = solid_key
        alias_to_name[alias] = solid_key.name
        aliased_dependencies_dict[alias] = input_dep_dict

        for dependency in input_dep_dict.values():
            for dep in dependency.get_definitions():
                name_to_aliases[dep.solid].add(dep.solid)

    pipeline_solid_dict = _build_pipeline_solid_dict(
        solid_defs, name_to_aliases, alias_to_solid_instance, container_definition
    )

    _validate_dependencies(aliased_dependencies_dict, pipeline_solid_dict, alias_to_name)

    dependency_structure = DependencyStructure.from_definitions(
        pipeline_solid_dict, aliased_dependencies_dict
    )

    return dependency_structure, pipeline_solid_dict


def _build_pipeline_solid_dict(
    solid_defs, name_to_aliases, alias_to_solid_instance, container_definition
):
    pipeline_solids = []
    for solid_def in solid_defs:
        uses_of_solid = name_to_aliases.get(solid_def.name, {solid_def.name})

        for alias in uses_of_solid:
            solid_instance = alias_to_solid_instance.get(alias)

            solid_instance_tags = solid_instance.tags if solid_instance else {}
            pipeline_solids.append(
                Solid(
                    name=alias,
                    definition=solid_def,
                    container_definition=container_definition,
                    tags=solid_instance_tags,
                )
            )

    return {ps.name: ps for ps in pipeline_solids}


def _validate_dependencies(dependencies, solid_dict, alias_to_name):
    for from_solid, dep_by_input in dependencies.items():
        for from_input, dep_def in dep_by_input.items():
            for dep in dep_def.get_definitions():

                if from_solid == dep.solid:
                    raise DagsterInvalidDefinitionError(
                        (
                            'Invalid dependencies: circular reference detected in solid "{from_solid}" input "{from_input}"'
                        ).format(from_solid=from_solid, from_input=from_input)
                    )

                if not from_solid in solid_dict:
                    aliased_solid = alias_to_name.get(from_solid)
                    if aliased_solid == from_solid:
                        raise DagsterInvalidDefinitionError(
                            'Invalid dependencies: solid "{solid}" in dependency dictionary not found in solid list'.format(
                                solid=from_solid
                            )
                        )
                    else:
                        raise DagsterInvalidDefinitionError(
                            (
                                'Invalid dependencies: solid "{aliased_solid}" (aliased by "{from_solid}" in dependency '
                                'dictionary) not found in solid list'
                            ).format(aliased_solid=aliased_solid, from_solid=from_solid)
                        )
                if not solid_dict[from_solid].definition.has_input(from_input):
                    input_list = solid_dict[from_solid].definition.input_dict.keys()
                    raise DagsterInvalidDefinitionError(
                        'Invalid dependencies: solid "{from_solid}" does not have input "{from_input}". '.format(
                            from_solid=from_solid, from_input=from_input
                        )
                        + 'Available inputs: {input_list}'.format(input_list=input_list)
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
                        'Invalid dependencies: solid "{dep.solid}" does not have output "{dep.output}". '
                        'Listed as dependency for solid "{from_solid} input "{from_input}"'.format(
                            dep=dep, from_solid=from_solid, from_input=from_input
                        )
                    )

                input_def = solid_dict[from_solid].definition.input_def_named(from_input)
                output_def = solid_dict[dep.solid].definition.output_def_named(dep.output)

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
                'type {output_def.dagster_type.display_name}{extra}.'
            ).format(
                from_solid=from_solid,
                dep=dep,
                output_def=output_def,
                input_def=input_def,
                extra=' (which produces no value)'
                if output_def.dagster_type.kind == DagsterTypeKind.NOTHING
                else '',
            )
        )
