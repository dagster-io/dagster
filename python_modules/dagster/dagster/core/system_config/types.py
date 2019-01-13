from dagster import check

from dagster.utils import camelcase, single_item

from dagster.core.definitions import (
    PipelineContextDefinition,
    PipelineDefinition,
    ResourceDefinition,
    Solid,
    SolidDefinition,
    SolidInputHandle,
)


from dagster.core.types import Bool, Field, List, NamedDict, NamedSelector
from dagster.core.types.config import ConfigType, ConfigTypeAttributes
from dagster.core.types.default_applier import apply_default_values
from dagster.core.types.field_utils import check_opt_field_param, FieldImpl

from .objects import (
    ContextConfig,
    EnvironmentConfig,
    ExecutionConfig,
    ExpectationsConfig,
    SolidConfig,
)


def SystemNamedDict(name, fields, description=None):
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


def define_resource_dictionary_cls(name, resources):
    check.str_param(name, 'name')
    check.dict_param(resources, 'resources', key_type=str, value_type=ResourceDefinition)

    fields = {}
    for resource_name, resource in resources.items():
        if resource.config_field:
            fields[resource_name] = Field(
                SystemNamedDict(name + '.' + resource_name, {'config': resource.config_field})
            )

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
        context_definition.resources,
    )


def remove_none_entries(ddict):
    return {k: v for k, v in ddict.items() if v is not None}


def define_solid_config_cls(name, config_field, inputs_field, outputs_field):
    check.str_param(name, 'name')
    check_opt_field_param(config_field, 'config_field')
    check_opt_field_param(inputs_field, 'inputs_field')
    check_opt_field_param(outputs_field, 'outputs_field')

    return NamedDict(
        name,
        remove_none_entries(
            {'config': config_field, 'inputs': inputs_field, 'outputs': outputs_field}
        ),
        type_attributes=ConfigTypeAttributes(is_system_config=True),
    )


def define_environment_cls(pipeline_def):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    pipeline_name = camelcase(pipeline_def.name)
    return SystemNamedDict(
        name='{pipeline_name}.Environment'.format(pipeline_name=pipeline_name),
        fields={
            'context': define_maybe_optional_selector_field(
                define_context_context_cls(pipeline_name, pipeline_def.context_definitions)
            ),
            'solids': Field(
                define_solid_dictionary_cls(
                    '{pipeline_name}.SolidsConfigDictionary'.format(pipeline_name=pipeline_name),
                    pipeline_def,
                )
            ),
            'expectations': Field(
                define_expectations_config_cls(
                    '{pipeline_name}.ExpectationsConfig'.format(pipeline_name=pipeline_name)
                )
            ),
            'execution': Field(
                define_execution_config_cls(
                    '{pipeline_name}.ExecutionConfig'.format(pipeline_name=pipeline_name)
                )
            ),
        },
    )


def define_expectations_config_cls(name):
    check.str_param(name, 'name')

    return SystemNamedDict(
        name, fields={'evaluate': Field(Bool, is_optional=True, default_value=True)}
    )


def solid_has_configurable_inputs(solid_def):
    check.inst_param(solid_def, 'solid_def', SolidDefinition)
    return any(map(lambda inp: inp.runtime_type.input_schema, solid_def.input_defs))


def solid_has_configurable_outputs(solid_def):
    check.inst_param(solid_def, 'solid_def', SolidDefinition)
    return any(map(lambda out: out.runtime_type.output_schema, solid_def.output_defs))


def get_inputs_field(pipeline_def, solid):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.inst_param(solid, 'solid', Solid)

    if not solid_has_configurable_inputs(solid.definition):
        return None

    inputs_field_fields = {}
    for inp in [inp for inp in solid.definition.input_defs if inp.runtime_type.input_schema]:
        inp_handle = SolidInputHandle(solid, inp)
        # If this input is not satisfied by a dependency you must
        # provide it via config
        if not pipeline_def.dependency_structure.has_dep(inp_handle):
            inputs_field_fields[inp.name] = FieldImpl(inp.runtime_type.input_schema.schema_type)

    if not inputs_field_fields:
        return None

    return Field(
        SystemNamedDict(
            '{pipeline_name}.{solid_name}.Inputs'.format(
                pipeline_name=camelcase(pipeline_def.name), solid_name=camelcase(solid.name)
            ),
            inputs_field_fields,
        )
    )


def get_outputs_field(pipeline_def, solid):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.inst_param(solid, 'solid', Solid)

    solid_def = solid.definition

    if not solid_has_configurable_outputs(solid_def):
        return None

    output_dict_fields = {}
    for out in [out for out in solid_def.output_defs if out.runtime_type.output_schema]:
        output_dict_fields[out.name] = Field(
            type(out.runtime_type.output_schema.schema_type), is_optional=True
        )

    output_entry_dict = SystemNamedDict(
        '{pipeline_name}.{solid_name}.Outputs'.format(
            pipeline_name=camelcase(pipeline_def.name), solid_name=camelcase(solid.name)
        ),
        output_dict_fields,
    )

    return Field(List(output_entry_dict), is_optional=True)


def solid_has_config_entry(solid_def):
    check.inst_param(solid_def, 'solid_def', SolidDefinition)
    return (
        solid_def.config_field
        or solid_has_configurable_inputs(solid_def)
        or solid_has_configurable_outputs(solid_def)
    )


def define_solid_dictionary_cls(name, pipeline_def):
    check.str_param(name, 'name')
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)

    fields = {}
    for solid in pipeline_def.solids:
        if solid_has_config_entry(solid.definition):
            solid_config_type = define_solid_config_cls(
                '{pipeline_name}.SolidConfig.{solid_name}'.format(
                    pipeline_name=camelcase(pipeline_def.name), solid_name=camelcase(solid.name)
                ),
                solid.definition.config_field,
                inputs_field=get_inputs_field(pipeline_def, solid),
                outputs_field=get_outputs_field(pipeline_def, solid),
            )
            fields[solid.name] = Field(solid_config_type)

    return SystemNamedDict(name, fields)


def define_execution_config_cls(name):
    check.str_param(name, 'name')
    return NamedDict(name, {}, type_attributes=ConfigTypeAttributes(is_system_config=True))


def construct_environment_config(config_value):
    return EnvironmentConfig(
        solids=construct_solid_dictionary(config_value['solids']),
        execution=ExecutionConfig(**config_value['execution']),
        expectations=ExpectationsConfig(**config_value['expectations']),
        context=construct_context_config(config_value['context']),
    )


def construct_context_config(config_value):
    context_name, context_value = single_item(config_value)
    return ContextConfig(
        name=context_name, config=context_value.get('config'), resources=context_value['resources']
    )


def construct_solid_dictionary(solid_dict_value):
    return {
        key: SolidConfig(
            config=value.get('config'),
            inputs=value.get('inputs', {}),
            outputs=value.get('outputs', []),
        )
        for key, value in solid_dict_value.items()
    }
