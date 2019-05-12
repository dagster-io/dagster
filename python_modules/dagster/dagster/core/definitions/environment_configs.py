from collections import namedtuple

from dagster import check
from dagster.core.system_config.objects import (
    ContextConfig,
    EnvironmentConfig,
    ExecutionConfig,
    ExpectationsConfig,
    SolidConfig,
    StorageConfig,
)
from dagster.core.types import Bool, Dict, Field, List, NamedDict, NamedSelector, String
from dagster.core.types.config import ConfigType, ConfigTypeAttributes
from dagster.core.types.default_applier import apply_default_values
from dagster.core.types.field_utils import FieldImpl, check_opt_field_param
from dagster.utils import camelcase, merge_dicts, single_item

from .context import PipelineContextDefinition
from .dependency import DependencyStructure, Solid, SolidHandle, SolidInputHandle
from .mode import ModeDefinition
from .resource import ResourceDefinition
from .solid import CompositeSolidDefinition, ISolidDefinition, SolidDefinition


def SystemNamedDict(name, fields, description=None):
    '''A SystemNamedDict object is simply a NamedDict intended for internal (dagster) use.
    '''
    return NamedDict(name, fields, description, ConfigTypeAttributes(is_system_config=True))


def SystemNamedSelector(name, fields, description=None):
    return NamedSelector(name, fields, description, ConfigTypeAttributes(is_system_config=True))


def _is_selector_field_optional(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)
    if len(config_type.fields) > 1:
        return False
    else:
        _name, field = single_item(config_type.fields)
        return field.is_optional


def define_maybe_optional_selector_field(config_cls):
    is_optional = _is_selector_field_optional(config_cls.inst())

    return (
        Field(
            config_cls,
            is_optional=is_optional,
            default_value=apply_default_values(config_cls.inst(), None),
        )
        if is_optional
        else Field(config_cls, is_optional=False)
    )


def define_resource_cls(parent_name, resource_name, resource_def):
    return SystemNamedDict(
        '{parent_name}.{resource_name}'.format(
            parent_name=parent_name, resource_name=camelcase(resource_name)
        ),
        {'config': resource_def.config_field},
    )


def define_resource_dictionary_cls(name, resources):
    check.str_param(name, 'name')
    check.dict_param(resources, 'resources', key_type=str, value_type=ResourceDefinition)

    fields = {}
    for resource_name, resource in resources.items():
        if resource.config_field:
            fields[resource_name] = Field(define_resource_cls(name, resource_name, resource))

    return SystemNamedDict(name=name, fields=fields)


def define_specific_context_config_cls(name, config_field, resources):
    check.str_param(name, 'name')
    check_opt_field_param(config_field, 'config_field')
    check.dict_param(resources, 'resources', key_type=str, value_type=ResourceDefinition)

    return SystemNamedDict(
        name,
        fields=remove_none_entries(
            {
                'config': config_field,
                'resources': Field(
                    define_resource_dictionary_cls('{name}.Resources'.format(name=name), resources)
                ),
                'persistence': Field(
                    SystemNamedSelector(
                        '{name}.Persistence'.format(name=name), {'file': Field(Dict({}))}
                    )
                ),
            }
        ),
    )


def define_context_context_cls(pipeline_name, context_definitions):
    check.str_param(pipeline_name, 'pipeline_name')
    check.dict_param(
        context_definitions,
        'context_definitions',
        key_type=str,
        value_type=PipelineContextDefinition,
    )
    full_type_name = '{pipeline_name}.ContextConfig'.format(pipeline_name=pipeline_name)
    field_dict = {}
    if len(context_definitions) == 1:
        context_name, context_definition = single_item(context_definitions)
        field_dict[context_name] = Field(
            define_specific_context_cls(pipeline_name, context_name, context_definition)
        )
    else:
        for context_name, context_definition in context_definitions.items():
            field_dict[context_name] = Field(
                define_specific_context_cls(pipeline_name, context_name, context_definition),
                is_optional=True,
            )

    return SystemNamedSelector(full_type_name, field_dict)


def define_specific_context_cls(pipeline_name, context_name, context_definition):
    return define_specific_context_config_cls(
        '{pipeline_name}.ContextDefinitionConfig.{context_name}'.format(
            pipeline_name=pipeline_name, context_name=camelcase(context_name)
        ),
        context_definition.config_field,
        context_definition.resource_defs,
    )


def remove_none_entries(ddict):
    return {k: v for k, v in ddict.items() if v is not None}


def define_solid_config_cls(name, config_field, inputs_field, outputs_field):
    check.str_param(name, 'name')
    check_opt_field_param(config_field, 'config_field')
    check_opt_field_param(inputs_field, 'inputs_field')
    check_opt_field_param(outputs_field, 'outputs_field')

    return SystemNamedDict(
        name,
        remove_none_entries(
            {'config': config_field, 'inputs': inputs_field, 'outputs': outputs_field}
        ),
    )


class EnvironmentClassCreationData(
    namedtuple(
        'EnvironmentClassCreationData',
        'pipeline_name solids context_definitions dependency_structure mode_definition',
    )
):
    def __new__(
        cls, pipeline_name, solids, context_definitions, dependency_structure, mode_definition
    ):
        return super(EnvironmentClassCreationData, cls).__new__(
            cls,
            pipeline_name=check.str_param(pipeline_name, 'pipeline_name'),
            solids=check.list_param(solids, 'solids', of_type=Solid),
            context_definitions=check.opt_dict_param(
                context_definitions,
                'context_definitions',
                key_type=str,
                value_type=PipelineContextDefinition,
            ),
            dependency_structure=check.inst_param(
                dependency_structure, 'dependency_structure', DependencyStructure
            ),
            mode_definition=check.opt_inst_param(
                mode_definition, 'mode_definition', ModeDefinition
            ),
        )


def define_context_cls(pipeline_def):
    from dagster import PipelineDefinition

    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    pipeline_name = camelcase(pipeline_def.name)
    return SystemNamedDict(
        name='{pipeline_name}.Context'.format(pipeline_name=pipeline_name),
        fields={
            'context': define_maybe_optional_selector_field(
                define_context_context_cls(pipeline_name, pipeline_def.context_definitions)
            )
        },
    )


def define_mode_resources_dictionary_cls(pipeline_name, mode_definition):
    check.str_param(pipeline_name, 'pipeline_name')
    check.inst_param(mode_definition, 'mode_definition', ModeDefinition)

    return define_resource_dictionary_cls(
        '{pipeline_name}.Mode.{mode}.Resources'.format(
            pipeline_name=pipeline_name, mode=camelcase(mode_definition.name)
        ),
        mode_definition.resource_defs,
    )


def get_additional_fields(pipeline_name, creation_data):
    if creation_data.mode_definition:
        check.invariant(not creation_data.context_definitions)
        return {
            'resources': Field(
                define_mode_resources_dictionary_cls(pipeline_name, creation_data.mode_definition)
            )
        }
    else:
        check.invariant(creation_data.context_definitions)
        return {
            'context': define_maybe_optional_selector_field(
                define_context_context_cls(pipeline_name, creation_data.context_definitions)
            )
        }


def define_environment_cls(creation_data):
    check.inst_param(creation_data, 'creation_data', EnvironmentClassCreationData)
    pipeline_name = camelcase(creation_data.pipeline_name)

    return SystemNamedDict(
        name='{pipeline_name}.Mode.{mode_name}.Environment'.format(
            pipeline_name=pipeline_name, mode_name=camelcase(creation_data.mode_definition.name)
        )
        if creation_data.mode_definition
        else '{pipeline_name}.Environment'.format(pipeline_name=pipeline_name),
        fields=remove_none_entries(
            merge_dicts(
                {
                    'solids': Field(
                        define_solid_dictionary_cls(
                            '{pipeline_name}.SolidsConfigDictionary'.format(
                                pipeline_name=pipeline_name
                            ),
                            creation_data.solids,
                            creation_data.dependency_structure,
                            creation_data.pipeline_name,
                        )
                    ),
                    'expectations': Field(
                        define_expectations_config_cls(
                            '{pipeline_name}.ExpectationsConfig'.format(pipeline_name=pipeline_name)
                        )
                    ),
                    'storage': Field(
                        define_storage_config_cls(
                            '{pipeline_name}.StorageConfig'.format(pipeline_name=pipeline_name)
                        ),
                        is_optional=True,
                    ),
                    'execution': Field(
                        define_execution_config_cls(
                            '{pipeline_name}.ExecutionConfig'.format(pipeline_name=pipeline_name)
                        )
                    ),
                },
                get_additional_fields(pipeline_name, creation_data),
            )
        ),
    )


def define_expectations_config_cls(name):
    check.str_param(name, 'name')

    return SystemNamedDict(
        name, fields={'evaluate': Field(Bool, is_optional=True, default_value=True)}
    )


def define_storage_config_cls(name):
    check.str_param(name, 'name')

    return SystemNamedSelector(
        name,
        {
            'in_memory': Field(
                SystemNamedDict('{parent_name}.InMem'.format(parent_name=name), {}),
                is_optional=True,
            ),
            'filesystem': Field(
                SystemNamedDict(
                    '{parent_name}.Files'.format(parent_name=name),
                    {'base_dir': Field(String, is_optional=True)},
                ),
                is_optional=True,
            ),
            's3': Field(
                SystemNamedDict(
                    '{parent_name}.S3'.format(parent_name=name), {'s3_bucket': Field(String)}
                ),
                is_optional=True,
            ),
        },
    )


def solid_has_configurable_inputs(solid_def):
    check.inst_param(solid_def, 'solid_def', ISolidDefinition)
    return any(map(lambda inp: inp.runtime_type.input_schema, solid_def.input_dict.values()))


def solid_has_configurable_outputs(solid_def):
    check.inst_param(solid_def, 'solid_def', ISolidDefinition)
    return any(map(lambda out: out.runtime_type.output_schema, solid_def.output_dict.values()))


def get_inputs_field(solid, handle, dependency_structure, pipeline_name):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(handle, 'handle', SolidHandle)
    check.inst_param(dependency_structure, 'dependency_structure', DependencyStructure)
    check.str_param(pipeline_name, 'pipeline_name')

    if not solid_has_configurable_inputs(solid.definition):
        return None

    inputs_field_fields = {}
    for name, inp in solid.definition.input_dict.items():
        if inp.runtime_type.input_schema:
            inp_handle = SolidInputHandle(solid, inp)
            # If this input is not satisfied by a dependency you must
            # provide it via config
            if not dependency_structure.has_dep(inp_handle) and not solid.parent_maps_input(name):
                inputs_field_fields[name] = FieldImpl(inp.runtime_type.input_schema.schema_type)

    if not inputs_field_fields:
        return None

    return Field(
        SystemNamedDict(
            '{pipeline_name}.{solid_handle}.Inputs'.format(
                pipeline_name=camelcase(pipeline_name), solid_handle=handle.camelcase()
            ),
            inputs_field_fields,
        )
    )


def get_outputs_field(solid, handle, pipeline_name):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(handle, 'handle', SolidHandle)
    check.str_param(pipeline_name, 'pipeline_name')

    solid_def = solid.definition

    if not solid_has_configurable_outputs(solid_def):
        return None

    output_dict_fields = {}
    for name, out in solid_def.output_dict.items():
        if out.runtime_type.output_schema:
            output_dict_fields[name] = Field(
                type(out.runtime_type.output_schema.schema_type), is_optional=True
            )

    output_entry_dict = SystemNamedDict(
        '{pipeline_name}.{solid_handle}.Outputs'.format(
            pipeline_name=camelcase(pipeline_name), solid_handle=handle.camelcase()
        ),
        output_dict_fields,
    )

    return Field(List(output_entry_dict), is_optional=True)


def solid_has_config_entry(solid_def):
    check.inst_param(solid_def, 'solid_def', ISolidDefinition)

    has_solid_config = False
    if isinstance(solid_def, CompositeSolidDefinition):
        has_solid_config = any(
            map(solid_has_config_entry, [solid.definition for solid in solid_def.solids])
        )
    elif isinstance(solid_def, SolidDefinition):
        has_solid_config = solid_def.config_field
    else:
        check.invariant('Unexpected ISolidDefinition type {type}'.format(type=type(solid_def)))

    return (
        has_solid_config
        or solid_has_configurable_inputs(solid_def)
        or solid_has_configurable_outputs(solid_def)
    )


def define_isolid_field(solid, handle, dependency_structure, pipeline_name):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(handle, 'handle', SolidHandle)

    check.str_param(pipeline_name, 'pipeline_name')

    if isinstance(solid.definition, CompositeSolidDefinition):
        composite_def = solid.definition
        solid_cfg = Field(
            define_solid_dictionary_cls(
                '{pipeline_name}.CompositeSolidsDict.{solid_handle}'.format(
                    pipeline_name=camelcase(pipeline_name), solid_handle=handle.camelcase()
                ),
                composite_def.solids,
                composite_def.dependency_structure,
                pipeline_name,
                handle,
            )
        )
        return Field(
            SystemNamedDict(
                '{name}CompositeSolidConfig'.format(name=str(handle)),
                remove_none_entries(
                    {
                        'solids': solid_cfg,
                        'inputs': get_inputs_field(
                            solid, handle, dependency_structure, pipeline_name
                        ),
                        'outputs': get_outputs_field(solid, handle, pipeline_name),
                    }
                ),
            )
        )

    elif isinstance(solid.definition, SolidDefinition):
        solid_config_type = define_solid_config_cls(
            '{pipeline_name}.SolidConfig.{solid_handle}'.format(
                pipeline_name=camelcase(pipeline_name), solid_handle=handle.camelcase()
            ),
            solid.definition.config_field,
            inputs_field=get_inputs_field(solid, handle, dependency_structure, pipeline_name),
            outputs_field=get_outputs_field(solid, handle, pipeline_name),
        )
        return Field(solid_config_type)
    else:
        check.invariant(
            'Unexpected ISolidDefinition type {type}'.format(type=type(solid.definition))
        )


def define_solid_dictionary_cls(
    name, solids, dependency_structure, pipeline_name, parent_handle=None
):
    check.str_param(name, 'name')
    check.list_param(solids, 'solids', of_type=Solid)
    check.inst_param(dependency_structure, 'dependency_structure', DependencyStructure)
    check.str_param(pipeline_name, 'pipeline_name')
    check.opt_inst_param(parent_handle, 'parent_handle', SolidHandle)

    fields = {}
    for solid in solids:
        if solid_has_config_entry(solid.definition):
            fields[solid.name] = define_isolid_field(
                solid,
                SolidHandle(solid.name, solid.definition.name, parent_handle),
                dependency_structure,
                pipeline_name,
            )

    return SystemNamedDict(name, fields)


def define_execution_config_cls(name):
    check.str_param(name, 'name')
    return SystemNamedDict(name, {})


def construct_environment_config(config_value):
    check.dict_param(config_value, 'config_value')

    return EnvironmentConfig(
        solids=construct_solid_dictionary(config_value['solids']),
        execution=ExecutionConfig(**config_value['execution']),
        expectations=ExpectationsConfig(**config_value['expectations']),
        context=construct_context_config(config_value['context'])
        if 'context' in config_value
        else None,
        storage=construct_storage_config(config_value.get('storage')),
        original_config_dict=config_value,
        resources=config_value.get('resources'),
    )


def construct_storage_config(config_value):
    check.opt_dict_param(config_value, 'config_value', key_type=str)
    if config_value:
        storage_mode, storage_config = single_item(config_value)
        return StorageConfig(storage_mode, storage_config)
    return StorageConfig(None, None)


def construct_context_config(config_value):
    context_name, context_value = single_item(config_value)
    return ContextConfig(
        name=context_name,
        config=context_value.get('config'),
        resources=context_value['resources'],
        persistence=context_value['persistence'],
    )


def construct_solid_dictionary(solid_dict_value, parent_handle=None, config_map=None):
    config_map = {} if config_map is None else config_map
    for name, value in solid_dict_value.items():
        key = SolidHandle(name, None, parent_handle)
        config = value.get('config')
        config_map[str(key)] = SolidConfig(
            config=config, inputs=value.get('inputs', {}), outputs=value.get('outputs', [])
        )
        # solids implies a composite solid config
        if value.get('solids'):
            construct_solid_dictionary(value['solids'], key, config_map)

    return config_map
