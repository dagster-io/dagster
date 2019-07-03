from enum import Enum as PythonEnum

import pytest

from dagster import (
    Dict,
    Enum,
    EnumValue,
    Field,
    Int,
    DagsterInvalidConfigError,
    PipelineDefinition,
    execute_pipeline,
    solid,
)
from dagster.core.types.config import ConfigEnum
from dagster.core.types.evaluator import evaluate_config


def define_test_enum_type():
    return ConfigEnum(name='TestEnum', enum_values=[EnumValue('VALUE_ONE')])


def test_config_enums():
    assert evaluate_config(define_test_enum_type(), 'VALUE_ONE').success


def test_config_enum_error_none():
    assert not evaluate_config(define_test_enum_type(), None).success


def test_config_enum_error_wrong_type():
    assert not evaluate_config(define_test_enum_type(), 384934).success


def test_config_enum_error():
    assert not evaluate_config(define_test_enum_type(), 'NOT_PRESENT').success


def test_enum_in_pipeline_execution():
    called = {}

    @solid(
        config_field=Field(
            Dict(
                {
                    'int_field': Field(Int),
                    'enum_field': Field(Enum('AnEnum', [EnumValue('ENUM_VALUE')])),
                }
            )
        )
    )
    def config_me(context):
        assert context.solid_config['int_field'] == 2
        assert context.solid_config['enum_field'] == 'ENUM_VALUE'
        called['yup'] = True

    pipeline_def = PipelineDefinition(name='enum_in_pipeline', solid_defs=[config_me])

    result = execute_pipeline(
        pipeline_def,
        {'solids': {'config_me': {'config': {'int_field': 2, 'enum_field': 'ENUM_VALUE'}}}},
    )

    assert result.success
    assert called['yup']

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        execute_pipeline(
            pipeline_def,
            {'solids': {'config_me': {'config': {'int_field': 2, 'enum_field': 'NOPE'}}}},
        )

    assert 'Error 1: Type failure at path "root:solids:config_me:config:enum_field"' in str(
        exc_info.value
    )


class NativeEnum(PythonEnum):
    FOO = 1
    BAR = 2


def test_native_enum_dagster_enum():
    dagster_enum = Enum(
        'DagsterNativeEnum',
        [
            EnumValue(config_value='FOO', python_value=NativeEnum.FOO),
            EnumValue(config_value='BAR', python_value=NativeEnum.BAR),
        ],
    )

    called = {}

    @solid(config_field=Field(dagster_enum))
    def dagster_enum_me(context):
        assert context.solid_config == NativeEnum.BAR
        called['yup'] = True

    pipeline_def = PipelineDefinition(
        name='native_enum_dagster_pipeline', solid_defs=[dagster_enum_me]
    )

    result = execute_pipeline(pipeline_def, {'solids': {'dagster_enum_me': {'config': 'BAR'}}})
    assert result.success
    assert called['yup']
