from dagster import check

from dagster.utils import camelcase

from .config import (
    Context,
    Environment,
    Execution,
    Expectations,
    Solid,
)

from .definitions import (
    Field,
    PipelineContextDefinition,
    PipelineDefinition,
)

from .evaluator import throwing_evaluate_config_value

from .types import (
    Bool,
    DagsterCompositeType,
    DagsterEvaluateConfigValueError,
    DagsterType,
    DagsterTypeAttributes,
)


class HasUserConfig:
    def __init__(self):
        check.inst(self, DagsterCompositeType, 'HasUserConfig must be mixined on Composite')
        check.invariant(
            'config' in self.field_dict,  # pylint: disable=E1101
            'HasUserConfig must have "config" field',
        )

    @property
    def user_config_field(self):
        return self.field_dict['config']  # pylint: disable=E1101


def define_possibly_optional_field(config_type, is_optional):
    check.inst_param(config_type, 'config_type', DagsterType)
    check.bool_param(is_optional, 'is_optional')

    return Field(
        config_type,
        is_optional=True,
        default_value=lambda: throwing_evaluate_config_value(config_type, None),
    ) if is_optional else Field(config_type)


class SpecificContextConfig(DagsterCompositeType, HasUserConfig):
    def __init__(self, name, config_type):
        check.str_param(name, 'name')
        config_field = define_possibly_optional_field(config_type, all_optional_type(config_type))
        super(SpecificContextConfig, self).__init__(
            name,
            {'config': config_field},
            type_attributes=DagsterTypeAttributes(is_system_config=True),
        )


def define_specific_context_field(
    pipeline_name,
    context_name,
    context_def,
    is_optional,
    provide_default=False,
):
    check.str_param(pipeline_name, 'pipeline_name')
    check.str_param(context_name, 'context_name')
    check.inst_param(context_def, 'context_def', PipelineContextDefinition)
    check.bool_param(is_optional, 'is_optional')
    check.bool_param(provide_default, 'provide_default')

    specific_context_config_type = SpecificContextConfig(
        '{pipeline_name}.ContextDefinitionConfig.{context_name}'.format(
            pipeline_name=pipeline_name,
            context_name=camelcase(context_name),
        ),
        context_def.config_def.config_type,
    )

    if is_optional and provide_default:
        return define_possibly_optional_field(specific_context_config_type, is_optional)

    return Field(specific_context_config_type, is_optional=is_optional)


def single_item(ddict):
    check.dict_param(ddict, 'ddict')
    check.param_invariant(len(ddict) == 1, 'ddict')
    return list(ddict.items())[0]


class ContextConfigType(DagsterCompositeType):
    def __init__(self, pipeline_name, context_definitions):
        check.str_param(pipeline_name, 'pipeline_name')
        check.dict_param(
            context_definitions,
            'context_definitions',
            key_type=str,
            value_type=PipelineContextDefinition,
        )

        full_type_name = '{pipeline_name}.ContextConfig'.format(pipeline_name=pipeline_name)

        field_dict = {}
        for context_name, context_definition in context_definitions.items():

            is_optional = True if len(context_definitions) > 1 else all_optional_type(
                context_definition.config_def.config_type,
            )

            field_dict[context_name] = define_specific_context_field(
                pipeline_name,
                context_name,
                context_definition,
                is_optional=is_optional,
                provide_default=is_optional and len(context_definitions) == 1,
            )

        super(ContextConfigType, self).__init__(
            full_type_name,
            field_dict,
            'A configuration dictionary with typed fields',
            type_attributes=DagsterTypeAttributes(is_system_config=True),
        )

    def construct_from_config_value(self, config_value):
        if not config_value:
            return None
        context_name, context_value = single_item(config_value)
        return Context(name=context_name, config=context_value['config'])


class SolidConfigType(DagsterCompositeType, HasUserConfig):
    def __init__(self, name, config_type):
        check.str_param(name, 'name')
        super(SolidConfigType, self).__init__(
            name,
            {
                'config': define_possibly_optional_field(
                    config_type,
                    all_optional_type(config_type),
                ),
            },
            type_attributes=DagsterTypeAttributes(is_system_config=True),
        )

    def construct_from_config_value(self, config_value):
        return Solid(**config_value)

    @property
    def user_config_field(self):
        return self.field_dict['config']


def define_environment_field(field_type):
    check.inst_param(field_type, 'field_type', DagsterType)
    return define_possibly_optional_field(field_type, all_optional_type(field_type))


def has_all_optional_default_context(pipeline_def):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    return 'default' in pipeline_def.context_definitions and all_optional_type(
        pipeline_def.context_definitions['default'].config_def.config_type
    )


def is_environment_context_field_optional(pipeline_def):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    if len(pipeline_def.context_definitions) > 1:
        return has_all_optional_default_context(pipeline_def)
    else:
        _, single_context_def = single_item(pipeline_def.context_definitions)

        return all_optional_type(single_context_def.config_def.config_type)


class EnvironmentConfigType(DagsterCompositeType):
    def __init__(self, pipeline_def):
        check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)

        pipeline_name = camelcase(pipeline_def.name)

        context_field = define_possibly_optional_field(
            ContextConfigType(pipeline_name, pipeline_def.context_definitions),
            is_environment_context_field_optional(pipeline_def),
        )

        solids_field = define_environment_field(
            SolidDictionaryType(
                '{pipeline_name}.SolidsConfigDictionary'.format(pipeline_name=pipeline_name),
                pipeline_def,
            )
        )

        expectations_field = define_environment_field(
            ExpectationsConfigType(
                '{pipeline_name}.ExpectationsConfig'.format(pipeline_name=pipeline_name)
            )
        )

        execution_field = define_environment_field(
            ExecutionConfigType(
                '{pipeline_name}.ExecutionConfig'.format(pipeline_name=pipeline_name)
            )
        )

        super(EnvironmentConfigType, self).__init__(
            '{pipeline_name}.Environment'.format(pipeline_name=pipeline_name),
            fields={
                'context': context_field,
                'solids': solids_field,
                'expectations': expectations_field,
                'execution': execution_field,
            },
            type_attributes=DagsterTypeAttributes(is_system_config=True),
        )

    def construct_from_config_value(self, config_value):
        return Environment(**config_value)


class ExpectationsConfigType(DagsterCompositeType):
    def __init__(self, name):
        super(ExpectationsConfigType, self).__init__(
            name,
            {'evaluate': Field(Bool, is_optional=True, default_value=True)},
            type_attributes=DagsterTypeAttributes(is_system_config=True),
        )

    def construct_from_config_value(self, config_value):
        return Expectations(**config_value)


def all_optional_type(dagster_type):
    check.inst_param(dagster_type, 'dagster_type', DagsterType)

    if isinstance(dagster_type, DagsterCompositeType):
        return dagster_type.all_fields_optional
    return True


def all_optional_user_config(config_type):
    check.inst_param(config_type, 'config_type', HasUserConfig)
    user_config_field = config_type.field_dict['config']
    return all_optional_type(user_config_field.dagster_type)


class SolidDictionaryType(DagsterCompositeType):
    def __init__(self, name, pipeline_def):
        check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)

        pipeline_name = camelcase(pipeline_def.name)
        field_dict = {}
        for solid in pipeline_def.solids:
            if solid.definition.config_def:
                solid_name = camelcase(solid.name)
                solid_config_type = SolidConfigType(
                    '{pipeline_name}.SolidConfig.{solid_name}'.format(
                        pipeline_name=pipeline_name,
                        solid_name=solid_name,
                    ),
                    solid.definition.config_def.config_type,
                )
                field_dict[solid.name] = define_possibly_optional_field(
                    solid_config_type,
                    all_optional_user_config(solid_config_type),
                )

        super(SolidDictionaryType, self).__init__(
            name,
            field_dict,
            type_attributes=DagsterTypeAttributes(is_system_config=True),
        )


class ExecutionConfigType(DagsterCompositeType):
    def __init__(self, name):
        check.str_param(name, 'name')
        super(ExecutionConfigType, self).__init__(
            name,
            {
                'serialize_intermediates': Field(Bool, is_optional=True, default_value=False),
            },
            type_attributes=DagsterTypeAttributes(is_system_config=True),
        )

    def construct_from_config_value(self, config_value):
        return Execution(**config_value)
