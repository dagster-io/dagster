import re
from dagster import check

from .config import (
    Context,
    Environment,
    Expectations,
    Solid,
)

from .definitions import (
    Field,
    PipelineContextDefinition,
    PipelineDefinition,
)

from .errors import DagsterTypeError

from .types import (
    Bool,
    ConfigDictionary,
    DagsterCompositeType,
    DagsterEvaluateValueError,
    DagsterType,
    process_incoming_composite_value,
)


def load_environment(pipeline_def, environment_dict):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.dict_param(environment_dict, 'environment_dict')

    env_type = EnvironmentConfigType(pipeline_def)
    return env_type.evaluate_value(environment_dict)


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
            field_dict[context_name] = Field(
                ConfigDictionary(
                    '{pipeline_name}.ContextDefinitionConfig.{context_name}'.format(
                        pipeline_name=pipeline_name,
                        context_name=camelcase(context_name),
                    ), {
                        'config': Field(context_definition.config_def.config_type),
                    }
                )
            )

        super(ContextConfigType, self).__init__(
            full_type_name,
            field_dict,
            'A configuration dictionary with typed fields',
        )

    def evaluate_value(self, value):
        if isinstance(value, Context):
            return value

        if value is not None and not isinstance(value, dict):
            raise DagsterEvaluateValueError('Incoming value for composite must be dict')

        if len(value) > 1:
            raise DagsterEvaluateValueError('You can only specify a single context')

        if not value:
            raise DagsterEvaluateValueError('Must specify a context')

        context_name, context_config_value = list(value.items())[0]

        parent_type = self.field_dict[context_name].dagster_type
        config_type = parent_type.field_dict['config'].dagster_type
        processed_value = config_type.evaluate_value(context_config_value['config'])
        return Context(context_name, processed_value)


class SolidConfigType(DagsterCompositeType):
    def __init__(self, name, config_type):
        check.str_param(name, 'name')
        super(SolidConfigType, self).__init__(name, {'config': Field(config_type)})

    def evaluate_value(self, value):
        if isinstance(value, Solid):
            return value

        return process_incoming_composite_value(self, value, lambda val: Solid(**val))


class EnvironmentConfigType(DagsterCompositeType):
    def __init__(self, pipeline_def):
        check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)

        pipeline_name = camelcase(pipeline_def.name)

        context_field = Field(
            ContextConfigType(
                pipeline_name,
                pipeline_def.context_definitions,
            ),
            is_optional=True,
        )

        solids_field = Field(
            SolidDictionaryType(
                '{pipeline_name}.SolidsConfigDictionary'.format(pipeline_name=pipeline_name),
                pipeline_def,
            ),
            is_optional=True,
        )

        expectations_field = Field(
            ExpectationsConfigType(
                '{pipeline_name}.ExpectationsConfig'.format(pipeline_name=pipeline_name)
            ),
            is_optional=True,
            default_value=Expectations(evaluate=True),
        )

        super(EnvironmentConfigType, self).__init__(
            '{pipeline_name}.Environment'.format(pipeline_name=pipeline_name),
            fields={
                'context': context_field,
                'solids': solids_field,
                'expectations': expectations_field,
            },
        )

    def evaluate_value(self, value):
        if value is None:
            return Environment()

        if isinstance(value, Environment):
            return value

        return process_incoming_composite_value(
            self,
            value,
            lambda val: Environment(**val),
        )


class ExpectationsConfigType(DagsterCompositeType):
    def __init__(self, name):
        super(ExpectationsConfigType, self).__init__(
            name,
            {'evaluate': Field(Bool)},
        )

    def evaluate_value(self, value):
        if isinstance(value, Expectations):
            return value

        return process_incoming_composite_value(self, value, lambda val: Expectations(**val))


class SolidDictionaryType(DagsterCompositeType):
    def __init__(self, name, pipeline_def):
        check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)

        pipeline_name = camelcase(pipeline_def.name)
        field_dict = {}
        for solid in pipeline_def.solids:
            if solid.definition.config_def:
                solid_name = camelcase(solid.name)
                field_dict[solid.name] = Field(
                    SolidConfigType(
                        '{pipeline_name}.{solid_name}.SolidConfig'.format(
                            pipeline_name=pipeline_name,
                            solid_name=solid_name,
                        ),
                        solid.definition.config_def.config_type,
                    )
                )

        super(SolidDictionaryType, self).__init__(name, field_dict)

    def evaluate_value(self, value):
        return process_incoming_composite_value(self, value, lambda val: val)


# Adapted from https://github.com/okunishinishi/python-stringcase/blob/master/stringcase.py
def camelcase(string):
    string = re.sub(r'^[\-_\.]', '', str(string))
    if not string:
        return string
    return str(string[0]).upper() + re.sub(
        r'[\-_\.\s]([a-z])',
        lambda matched: str(matched.group(1)).upper(),
        string[1:],
    )
