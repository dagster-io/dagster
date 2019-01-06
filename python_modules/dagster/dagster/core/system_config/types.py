from dagster import check

from dagster.utils import camelcase

from dagster.core.definitions import (
    PipelineContextDefinition,
    PipelineDefinition,
    ResourceDefinition,
    Solid,
    SolidDefinition,
    SolidInputHandle,
)


from dagster.core.types import Bool, Field, List
from dagster.core.types.config import ConfigType, ConfigTypeAttributes
from dagster.core.types.field import ConfigComposite, ConfigSelector, NamedDict

from dagster.core.types.evaluator import hard_create_config_value

from .objects import (
    ContextConfig,
    EnvironmentConfig,
    ExecutionConfig,
    ExpectationsConfig,
    SolidConfig,
)


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
            default_value=lambda: hard_create_config_value(config_cls.inst(), None),
        )
        if is_optional
        else Field(config_cls, is_optional=False)
    )


def define_specific_resource_config_cls(name, config_field):
    class _SpecificResourceConfig(ConfigComposite):
        def __init__(self):
            super(_SpecificResourceConfig, self).__init__(
                name=name, fields={'config': config_field}
            )

    return _SpecificResourceConfig


def define_resource_dictionary_cls(name, resources):
    check.str_param(name, 'name')
    check.dict_param(resources, 'resources', key_type=str, value_type=ResourceDefinition)

    class _ResourceDictionaryType(ConfigComposite):
        def __init__(self):
            field_dict = {}

            for resource_name, resource in resources.items():
                if resource.config_field:
                    specific_resource_type = define_specific_resource_config_cls(
                        name + '.' + resource_name, resource.config_field
                    )
                    field_dict[resource_name] = Field(specific_resource_type)

            super(_ResourceDictionaryType, self).__init__(
                name=name,
                fields=field_dict,
                type_attributes=ConfigTypeAttributes(is_system_config=True),
            )

    return _ResourceDictionaryType


def define_specific_context_config_cls(name, config_field, resources):
    check.str_param(name, 'name')
    check.opt_inst_param(config_field, 'config_field', Field)
    check.dict_param(resources, 'resources', key_type=str, value_type=ResourceDefinition)

    class _SpecificContextConfig(ConfigComposite):
        def __init__(self):
            resource_dict_type = define_resource_dictionary_cls(
                '{name}.Resources'.format(name=name), resources
            )
            super(_SpecificContextConfig, self).__init__(
                name=name,
                fields={'config': config_field, 'resources': Field(resource_dict_type)}
                if config_field
                else {'resources': Field(resource_dict_type)},
                type_attributes=ConfigTypeAttributes(is_system_config=True),
            )

    return _SpecificContextConfig


def single_item(ddict):
    check.dict_param(ddict, 'ddict')
    check.param_invariant(len(ddict) == 1, 'ddict')
    return list(ddict.items())[0]


def define_context_context_cls(pipeline_name, context_definitions):
    check.str_param(pipeline_name, 'pipeline_name')
    check.dict_param(
        context_definitions,
        'context_definitions',
        key_type=str,
        value_type=PipelineContextDefinition,
    )

    class _ContextConfigType(ConfigSelector):
        def __init__(self):
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
                        define_specific_context_cls(
                            pipeline_name, context_name, context_definition
                        ),
                        is_optional=True,
                    )

            super(_ContextConfigType, self).__init__(
                name=full_type_name,
                fields=field_dict,
                description='A configuration dictionary with typed fields',
                type_attributes=ConfigTypeAttributes(is_system_config=True),
            )

        def construct_from_config_value(self, config_value):
            context_name, context_value = single_item(config_value)
            return ContextConfig(
                name=context_name,
                config=context_value.get('config'),
                resources=context_value['resources'],
            )

    return _ContextConfigType


def define_specific_context_cls(pipeline_name, context_name, context_definition):
    return define_specific_context_config_cls(
        '{pipeline_name}.ContextDefinitionConfig.{context_name}'.format(
            pipeline_name=pipeline_name, context_name=camelcase(context_name)
        ),
        context_definition.config_field,
        context_definition.resources,
    )


def define_solid_config_cls(name, config_field, inputs_field, outputs_field):
    check.str_param(name, 'name')
    check.opt_inst_param(config_field, 'config_field', Field)
    check.opt_inst_param(inputs_field, 'inputs_field', Field)
    check.opt_inst_param(outputs_field, 'outputs_field', Field)

    class _SolidConfigType(ConfigComposite):
        def __init__(self):
            fields = {}
            if config_field:
                fields['config'] = config_field
            if inputs_field:
                fields['inputs'] = inputs_field
            if outputs_field:
                fields['outputs'] = outputs_field

            super(_SolidConfigType, self).__init__(
                name=name,
                fields=fields,
                type_attributes=ConfigTypeAttributes(is_system_config=True),
            )

        def construct_from_config_value(self, config_value):
            # TODO we need better rules around optional and default evaluation
            # making this permissive for now
            return SolidConfig(
                config=config_value.get('config'),
                inputs=config_value.get('inputs', {}),
                outputs=config_value.get('outputs', []),
            )

    return _SolidConfigType


def define_environment_cls(pipeline_def):
    class _EnvironmentConfigType(ConfigComposite):
        def __init__(self):
            check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)

            pipeline_name = camelcase(pipeline_def.name)

            context_field = define_maybe_optional_selector_field(
                define_context_context_cls(pipeline_name, pipeline_def.context_definitions)
            )

            solids_field = Field(
                define_solid_dictionary_cls(
                    '{pipeline_name}.SolidsConfigDictionary'.format(pipeline_name=pipeline_name),
                    pipeline_def,
                )
            )

            expectations_field = Field(
                define_expectations_config_cls(
                    '{pipeline_name}.ExpectationsConfig'.format(pipeline_name=pipeline_name)
                )
            )

            execution_field = Field(
                define_execution_config_cls(
                    '{pipeline_name}.ExecutionConfig'.format(pipeline_name=pipeline_name)
                )
            )

            super(_EnvironmentConfigType, self).__init__(
                name='{pipeline_name}.Environment'.format(pipeline_name=pipeline_name),
                fields={
                    'context': context_field,
                    'solids': solids_field,
                    'expectations': expectations_field,
                    'execution': execution_field,
                },
                type_attributes=ConfigTypeAttributes(is_system_config=True),
            )

        def construct_from_config_value(self, config_value):
            return EnvironmentConfig(**config_value)

    return _EnvironmentConfigType


def define_expectations_config_cls(name):
    check.str_param(name, 'name')

    class _ExpectationsConfigType(ConfigComposite):
        def __init__(self):
            super(_ExpectationsConfigType, self).__init__(
                name=name,
                fields={'evaluate': Field(Bool, is_optional=True, default_value=True)},
                type_attributes=ConfigTypeAttributes(is_system_config=True),
            )

        def construct_from_config_value(self, config_value):
            return ExpectationsConfig(**config_value)

    return _ExpectationsConfigType


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
            inputs_field_fields[inp.name] = Field(type(inp.runtime_type.input_schema))

    if not inputs_field_fields:
        return None

    return Field(
        NamedDict(
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
        output_dict_fields[out.name] = Field(type(out.runtime_type.output_schema), is_optional=True)

    output_entry_dict = NamedDict(
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

    class _SolidDictionaryType(ConfigComposite):
        def __init__(self):
            field_dict = {}
            for solid in pipeline_def.solids:
                if solid_has_config_entry(solid.definition):
                    solid_config_type = define_solid_config_cls(
                        '{pipeline_name}.SolidConfig.{solid_name}'.format(
                            pipeline_name=camelcase(pipeline_def.name),
                            solid_name=camelcase(solid.name),
                        ),
                        solid.definition.config_field,
                        inputs_field=get_inputs_field(pipeline_def, solid),
                        outputs_field=get_outputs_field(pipeline_def, solid),
                    )
                    field_dict[solid.name] = Field(solid_config_type)

            super(_SolidDictionaryType, self).__init__(
                name=name,
                fields=field_dict,
                type_attributes=ConfigTypeAttributes(is_system_config=True),
            )

    return _SolidDictionaryType


def define_execution_config_cls(name):
    check.str_param(name, 'name')

    class _ExecutionConfigType(ConfigComposite):
        def __init__(self):
            super(_ExecutionConfigType, self).__init__(
                name=name,
                fields={
                    'serialize_intermediates': Field(Bool, is_optional=True, default_value=False)
                },
                type_attributes=ConfigTypeAttributes(is_system_config=True),
            )

        def construct_from_config_value(self, config_value):
            return ExecutionConfig(**config_value)

    return _ExecutionConfigType
