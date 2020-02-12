from enum import Enum as PythonEnum

import pytest

from dagster import (
    DagsterInvalidConfigError,
    Enum,
    EnumValue,
    Int,
    PipelineDefinition,
    execute_pipeline,
    solid,
)
from dagster.config import Enum as ConfigEnum
from dagster.config.validate import validate_config


def define_test_enum_type():
    return ConfigEnum(name='TestEnum', enum_values=[EnumValue('VALUE_ONE')])


def test_config_enums():
    assert validate_config(define_test_enum_type(), 'VALUE_ONE').success


def test_config_enum_error_none():
    assert not validate_config(define_test_enum_type(), None).success


def test_config_enum_error_wrong_type():
    assert not validate_config(define_test_enum_type(), 384934).success


def test_config_enum_error():
    assert not validate_config(define_test_enum_type(), 'NOT_PRESENT').success


def test_enum_in_pipeline_execution():
    called = {}

    @solid(
        config={'int_field': Int, 'enum_field': Enum('AnEnum', [EnumValue('ENUM_VALUE')]),}
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

    @solid(config=dagster_enum)
    def dagster_enum_me(context):
        assert context.solid_config == NativeEnum.BAR
        called['yup'] = True

    pipeline_def = PipelineDefinition(
        name='native_enum_dagster_pipeline', solid_defs=[dagster_enum_me]
    )

    result = execute_pipeline(pipeline_def, {'solids': {'dagster_enum_me': {'config': 'BAR'}}})
    assert result.success
    assert called['yup']


def test_native_enum_dagster_enum_from_classmethod():
    dagster_enum = Enum.from_python_enum(NativeEnum)
    called = {}

    @solid(config=dagster_enum)
    def dagster_enum_me(context):
        assert context.solid_config == NativeEnum.BAR
        called['yup'] = True

    pipeline_def = PipelineDefinition(
        name='native_enum_dagster_pipeline', solid_defs=[dagster_enum_me]
    )

    result = execute_pipeline(pipeline_def, {'solids': {'dagster_enum_me': {'config': 'BAR'}}})
    assert result.success
    assert called['yup']


def test_native_enum_classmethod_creates_all_values():
    dagster_enum = Enum.from_python_enum(NativeEnum)
    for enum_value in NativeEnum:
        assert enum_value is dagster_enum.post_process(enum_value.name)
