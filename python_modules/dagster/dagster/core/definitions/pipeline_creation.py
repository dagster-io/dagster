from collections import defaultdict

from dagster.core.types.runtime import ALL_RUNTIME_BUILTINS
from dagster.core.errors import DagsterInvalidDefinitionError


from .dependency import DependencyStructure, SolidInstance, Solid


def _build_pipeline_solid_dict(solids, name_to_aliases, alias_to_solid_instance):
    pipeline_solids = []
    for solid_def in solids:
        uses_of_solid = name_to_aliases.get(solid_def.name, {solid_def.name})

        for alias in uses_of_solid:
            solid_instance = alias_to_solid_instance.get(alias)
            resource_mapper_fn = (
                solid_instance.resource_mapper_fn
                if solid_instance
                else SolidInstance.default_resource_mapper_fn
            )
            pipeline_solids.append(
                Solid(name=alias, definition=solid_def, resource_mapper_fn=resource_mapper_fn)
            )

    return {ps.name: ps for ps in pipeline_solids}


def create_execution_structure(solids, dependencies_dict):
    '''This builder takes the dependencies dictionary specified during creation of the
    PipelineDefinition object and builds (1) the execution structure and (2) a solid dependency
    dictionary.

    For example, for the following dependencies:

    dep_dict = {
            SolidInstance('giver'): {},
            SolidInstance('sleeper', alias='sleeper_1'): {
                'units': DependencyDefinition('giver', 'out_1')
            },
            SolidInstance('sleeper', alias='sleeper_2'): {
                'units': DependencyDefinition('giver', 'out_2')
            },
            SolidInstance('sleeper', alias='sleeper_3'): {
                'units': DependencyDefinition('giver', 'out_3')
            },
            SolidInstance('sleeper', alias='sleeper_4'): {
                'units': DependencyDefinition('giver', 'out_4')
            },
            SolidInstance('total'): {
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
    # Same as dep_dict but with SolidInstance replaced by alias string
    aliased_dependencies_dict = {}

    # Keep track of solid name -> all aliases used and alias -> name
    name_to_aliases = defaultdict(set)
    alias_to_solid_instance = {}
    alias_to_name = {}

    for solid_key, input_dep_dict in dependencies_dict.items():
        # We allow deps of the form dependencies={'foo': DependencyDefition('bar')}
        # Here, we replace 'foo' with SolidInstance('foo')
        if not isinstance(solid_key, SolidInstance):
            solid_key = SolidInstance(solid_key)

        alias = solid_key.alias or solid_key.name

        name_to_aliases[solid_key.name].add(alias)
        alias_to_solid_instance[alias] = solid_key
        alias_to_name[alias] = solid_key.name
        aliased_dependencies_dict[alias] = input_dep_dict

        for dependency in input_dep_dict.values():
            name_to_aliases[dependency.solid].add(dependency.solid)

    pipeline_solid_dict = _build_pipeline_solid_dict(
        solids, name_to_aliases, alias_to_solid_instance
    )

    _validate_dependencies(aliased_dependencies_dict, pipeline_solid_dict, alias_to_name)

    dependency_structure = DependencyStructure.from_definitions(
        pipeline_solid_dict, aliased_dependencies_dict
    )

    return dependency_structure, pipeline_solid_dict


def _validate_dependencies(dependencies, solid_dict, alias_to_name):
    for from_solid, dep_by_input in dependencies.items():
        for from_input, dep in dep_by_input.items():
            if from_solid == dep.solid:
                raise DagsterInvalidDefinitionError(
                    'Circular reference detected in solid {from_solid} input {from_input}.'.format(
                        from_solid=from_solid, from_input=from_input
                    )
                )

            if not from_solid in solid_dict:
                aliased_solid = alias_to_name.get(from_solid)
                if aliased_solid == from_solid:
                    raise DagsterInvalidDefinitionError(
                        'Solid {solid} in dependency dictionary not found in solid list'.format(
                            solid=from_solid
                        )
                    )
                else:
                    raise DagsterInvalidDefinitionError(
                        (
                            'Solid {aliased_solid} (aliased by {from_solid} in dependency '
                            'dictionary) not found in solid list'
                        ).format(aliased_solid=aliased_solid, from_solid=from_solid)
                    )
            if not solid_dict[from_solid].definition.has_input(from_input):
                input_list = solid_dict[from_solid].definition.input_dict.keys()
                raise DagsterInvalidDefinitionError(
                    'Solid "{from_solid}" does not have input "{from_input}". '.format(
                        from_solid=from_solid, from_input=from_input
                    )
                    + 'Input list: {input_list}'.format(input_list=input_list)
                )

            if not dep.solid in solid_dict:
                raise DagsterInvalidDefinitionError(
                    'Solid {dep.solid} in DependencyDefinition not found in solid list'.format(
                        dep=dep
                    )
                )

            if not solid_dict[dep.solid].definition.has_output(dep.output):
                raise DagsterInvalidDefinitionError(
                    'Solid {dep.solid} does not have output {dep.output}'.format(dep=dep)
                )

            input_def = solid_dict[from_solid].definition.input_def_named(from_input)
            output_def = solid_dict[dep.solid].definition.output_def_named(dep.output)

            _validate_input_output_pair(input_def, output_def, from_solid, dep)


def _validate_input_output_pair(input_def, output_def, from_solid, dep):
    # Currently, we opt to be overly permissive with input/output type mismatches.

    # Here we check for the case where no value will be provided where one is expected.
    if output_def.runtime_type.is_nothing and not input_def.runtime_type.is_nothing:
        raise DagsterInvalidDefinitionError(
            (
                'Input "{input_def.name}" to solid "{from_solid}" can not depend on the output '
                '"{output_def.name}" from solid "{dep.solid}". '
                'Input "{input_def.name} expects a value of type {input_def.runtime_type.name} '
                'and output "{output_def.name}" returns type {output_def.runtime_type.name}{extra}.'
            ).format(
                from_solid=from_solid,
                dep=dep,
                output_def=output_def,
                input_def=input_def,
                extra=' (which produces no value)' if output_def.runtime_type.is_nothing else '',
            )
        )


def construct_runtime_type_dictionary(solid_defs):
    type_dict = {t.name: t for t in ALL_RUNTIME_BUILTINS}
    for solid_def in solid_defs:
        for input_def in solid_def.input_dict.values():
            type_dict[input_def.runtime_type.name] = input_def.runtime_type
            for inner_type in input_def.runtime_type.inner_types:
                type_dict[inner_type.name] = inner_type

        for output_def in solid_def.output_dict.values():
            type_dict[output_def.runtime_type.name] = output_def.runtime_type
            for inner_type in output_def.runtime_type.inner_types:
                type_dict[inner_type.name] = inner_type

    return type_dict
