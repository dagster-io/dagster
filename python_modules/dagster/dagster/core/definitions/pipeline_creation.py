from collections import defaultdict
from dagster import check

from dagster.core.types import config
from dagster.core.types.iterate_types import iterate_config_types
from dagster.core.types.config import ALL_CONFIG_BUILTINS
from dagster.core.types.runtime import ALL_RUNTIME_BUILTINS
from dagster.core.errors import DagsterInvalidDefinitionError

from .context import PipelineContextDefinition

from .dependency import DependencyStructure, SolidInstance, Solid

from .solid import SolidDefinition


class SolidAliasMapper:
    def __init__(self, dependencies_dict):
        aliased_dependencies_dict = {}
        solid_uses = defaultdict(set)
        alias_lookup = {}

        for solid_key, input_dep_dict in dependencies_dict.items():
            if not isinstance(solid_key, SolidInstance):
                solid_key = SolidInstance(solid_key)

            if solid_key.alias:
                key = solid_key.name
                alias = solid_key.alias
            else:
                key = solid_key.name
                alias = solid_key.name

            solid_uses[key].add(alias)
            aliased_dependencies_dict[alias] = input_dep_dict
            alias_lookup[alias] = key

            for dependency in input_dep_dict.values():
                solid_uses[dependency.solid].add(dependency.solid)

        self.solid_uses = solid_uses
        self.aliased_dependencies_dict = aliased_dependencies_dict
        self.alias_lookup = alias_lookup

    def get_uses_of_solid(self, solid_def_name):
        return self.solid_uses.get(solid_def_name)


def create_execution_structure(solids, dependencies_dict):
    check.list_param(solids, 'solids', of_type=SolidDefinition)
    mapper = SolidAliasMapper(dependencies_dict)

    pipeline_solids = []
    for solid_def in solids:
        uses_of_solid = mapper.get_uses_of_solid(solid_def.name) or set([solid_def.name])

        for alias in uses_of_solid:
            pipeline_solids.append(Solid(name=alias, definition=solid_def))

    pipeline_solid_dict = {ps.name: ps for ps in pipeline_solids}

    _validate_dependencies(
        mapper.aliased_dependencies_dict, pipeline_solid_dict, mapper.alias_lookup
    )

    dependency_structure = DependencyStructure.from_definitions(
        pipeline_solid_dict, mapper.aliased_dependencies_dict
    )

    return dependency_structure, pipeline_solid_dict


def _validate_dependencies(dependencies, solid_dict, alias_lookup):
    for from_solid, dep_by_input in dependencies.items():
        for from_input, dep in dep_by_input.items():
            if from_solid == dep.solid:
                raise DagsterInvalidDefinitionError(
                    'Circular reference detected in solid {from_solid} input {from_input}.'.format(
                        from_solid=from_solid, from_input=from_input
                    )
                )

            if not from_solid in solid_dict:
                aliased_solid = alias_lookup.get(from_solid)
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
                input_list = [
                    input_def.name for input_def in solid_dict[from_solid].definition.input_defs
                ]
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


def iterate_solid_def_types(solid_def):
    if solid_def.config_field:
        for runtime_type in iterate_config_types(solid_def.config_field.config_type):
            yield runtime_type


def _gather_all_config_types(solid_defs, context_definitions, environment_type):
    check.list_param(solid_defs, 'solid_defs', SolidDefinition)
    check.dict_param(
        context_definitions,
        'context_definitions',
        key_type=str,
        value_type=PipelineContextDefinition,
    )

    check.inst_param(environment_type, 'environment_type', config.ConfigType)

    for solid_def in solid_defs:
        for runtime_type in iterate_solid_def_types(solid_def):
            yield runtime_type

    for context_definition in context_definitions.values():
        if context_definition.config_field:
            context_config_type = context_definition.config_field.config_type
            for runtime_type in iterate_config_types(context_config_type):
                yield runtime_type

    for runtime_type in iterate_config_types(environment_type):
        yield runtime_type


def construct_runtime_type_dictionary(solid_defs):
    type_dict = {t.name: t for t in ALL_RUNTIME_BUILTINS}
    for solid_def in solid_defs:
        for input_def in solid_def.input_defs:
            type_dict[input_def.runtime_type.name] = input_def.runtime_type
            for inner_type in input_def.runtime_type.inner_types:
                type_dict[inner_type.name] = inner_type

        for output_def in solid_def.output_defs:
            type_dict[output_def.runtime_type.name] = output_def.runtime_type
            for inner_type in output_def.runtime_type.inner_types:
                type_dict[inner_type.name] = inner_type

    return type_dict


def _gather_all_schemas(solid_defs):
    runtime_types = construct_runtime_type_dictionary(solid_defs)
    for rtt in runtime_types.values():
        if rtt.input_schema:
            for ct in iterate_config_types(rtt.input_schema.schema_type):
                yield ct
        if rtt.output_schema:
            for ct in iterate_config_types(rtt.output_schema.schema_type):
                yield ct


def construct_config_type_dictionary(solid_defs, context_definitions, environment_type):
    check.list_param(solid_defs, 'solid_defs', SolidDefinition)
    check.dict_param(
        context_definitions,
        'context_definitions',
        key_type=str,
        value_type=PipelineContextDefinition,
    )
    check.inst_param(environment_type, 'environment_type', config.ConfigType)

    type_dict_by_name = {t.name: t for t in ALL_CONFIG_BUILTINS}
    type_dict_by_key = {t.key: t for t in ALL_CONFIG_BUILTINS}
    all_types = list(
        _gather_all_config_types(solid_defs, context_definitions, environment_type)
    ) + list(_gather_all_schemas(solid_defs))

    for config_type in all_types:
        name = config_type.name
        if name and name in type_dict_by_name:
            if type(config_type) is not type(type_dict_by_name[name]):
                raise DagsterInvalidDefinitionError(
                    (
                        'Type names must be unique. You have constructed two different '
                        'instances of types with the same name "{name}".'
                    ).format(name=name)
                )
        else:
            type_dict_by_name[config_type.name] = config_type

        key = config_type.key

        if key in type_dict_by_key:
            if type(config_type) is not type(type_dict_by_key[key]):
                raise DagsterInvalidDefinitionError(
                    (
                        'Type keys must be unique. You have constructed two different '
                        'instances of types with the same key "{key}".'
                    ).format(key=key)
                )

        else:
            type_dict_by_key[config_type.key] = config_type

    return type_dict_by_name, type_dict_by_key
