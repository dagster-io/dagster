from enum import Enum as PythonEnum

import pytest
from dagster import (
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
    Enum,
    EnumValue,
    Field,
    Int,
    PipelineDefinition,
    execute_pipeline,
    pipeline,
    solid,
)
from dagster.config import Enum as ConfigEnum
from dagster.config.validate import validate_config


def define_test_enum_type():
    return ConfigEnum(name="TestEnum", enum_values=[EnumValue("VALUE_ONE")])


def test_config_enums():
    assert validate_config(define_test_enum_type(), "VALUE_ONE").success


def test_config_enum_error_none():
    assert not validate_config(define_test_enum_type(), None).success


def test_config_enum_error_wrong_type():
    assert not validate_config(define_test_enum_type(), 384934).success


def test_config_enum_error():
    assert not validate_config(define_test_enum_type(), "NOT_PRESENT").success


def test_enum_in_pipeline_execution():
    called = {}

    @solid(
        config_schema={
            "int_field": Int,
            "enum_field": Enum("AnEnum", [EnumValue("ENUM_VALUE")]),
        }
    )
    def config_me(context):
        assert context.solid_config["int_field"] == 2
        assert context.solid_config["enum_field"] == "ENUM_VALUE"
        called["yup"] = True

    pipeline_def = PipelineDefinition(name="enum_in_pipeline", solid_defs=[config_me])

    result = execute_pipeline(
        pipeline_def,
        {"solids": {"config_me": {"config": {"int_field": 2, "enum_field": "ENUM_VALUE"}}}},
    )

    assert result.success
    assert called["yup"]

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        execute_pipeline(
            pipeline_def,
            {"solids": {"config_me": {"config": {"int_field": 2, "enum_field": "NOPE"}}}},
        )

    assert (
        "Value at path root:solids:config_me:config:enum_field not in enum type AnEnum got NOPE"
        in str(exc_info.value)
    )


class NativeEnum(PythonEnum):
    FOO = 1
    BAR = 2


def test_native_enum_dagster_enum():
    dagster_enum = Enum(
        "DagsterNativeEnum",
        [
            EnumValue(config_value="FOO", python_value=NativeEnum.FOO),
            EnumValue(config_value="BAR", python_value=NativeEnum.BAR),
        ],
    )

    called = {}

    @solid(config_schema=dagster_enum)
    def dagster_enum_me(context):
        assert context.solid_config == NativeEnum.BAR
        called["yup"] = True

    pipeline_def = PipelineDefinition(
        name="native_enum_dagster_pipeline", solid_defs=[dagster_enum_me]
    )

    result = execute_pipeline(pipeline_def, {"solids": {"dagster_enum_me": {"config": "BAR"}}})
    assert result.success
    assert called["yup"]


def test_native_enum_dagster_enum_from_classmethod():
    dagster_enum = Enum.from_python_enum(NativeEnum)
    called = {}

    @solid(config_schema=dagster_enum)
    def dagster_enum_me(context):
        assert context.solid_config == NativeEnum.BAR
        called["yup"] = True

    pipeline_def = PipelineDefinition(
        name="native_enum_dagster_pipeline", solid_defs=[dagster_enum_me]
    )

    result = execute_pipeline(pipeline_def, {"solids": {"dagster_enum_me": {"config": "BAR"}}})
    assert result.success
    assert called["yup"]


def test_native_enum_not_allowed_as_default_value():
    dagster_enum = Enum.from_python_enum(NativeEnum)

    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:

        @solid(config_schema=Field(dagster_enum, is_required=False, default_value=NativeEnum.BAR))
        def _enum_direct(_):
            pass

    assert str(exc_info.value) == (
        "You have passed into a python enum value as the default value into "
        "of a config enum type NativeEnum. You must pass in the underlying string "
        "represention as the default value. One of ['FOO', 'BAR']."
    )


def test_list_enum_with_default_value():
    dagster_enum = Enum.from_python_enum(NativeEnum)

    called = {}

    @solid(config_schema=Field([dagster_enum], is_required=False, default_value=["BAR"]))
    def enum_list(context):
        assert context.solid_config == [NativeEnum.BAR]
        called["yup"] = True

    @pipeline
    def enum_list_pipeline():
        enum_list()

    result = execute_pipeline(enum_list_pipeline)

    assert result.success
    assert called["yup"]


def test_dict_enum_with_default():
    dagster_enum = Enum.from_python_enum(NativeEnum)

    called = {}

    @solid(config_schema={"enum": Field(dagster_enum, is_required=False, default_value="BAR")})
    def enum_dict(context):
        assert context.solid_config["enum"] == NativeEnum.BAR
        called["yup"] = True

    @pipeline
    def enum_dict_pipeline():
        enum_dict()

    result = execute_pipeline(enum_dict_pipeline)

    assert result.success
    assert called["yup"]


def test_list_enum_with_bad_default_value():
    dagster_enum = Enum.from_python_enum(NativeEnum)

    with pytest.raises(DagsterInvalidConfigError) as exc_info:

        @solid(
            config_schema=Field([dagster_enum], is_required=False, default_value=[NativeEnum.BAR])
        )
        def _bad_enum_list(_):
            pass

    # This error message is bad
    # https://github.com/dagster-io/dagster/issues/2339
    assert "Invalid default_value for Field." in str(exc_info.value)
    assert "Error 1: Value at path root[0] for enum type NativeEnum must be a string" in str(
        exc_info.value
    )


def test_dict_enum_with_bad_default():
    dagster_enum = Enum.from_python_enum(NativeEnum)

    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:

        @solid(
            config_schema={
                "enum": Field(dagster_enum, is_required=False, default_value=NativeEnum.BAR)
            }
        )
        def _enum_bad_dict(_):
            pass

    assert str(exc_info.value) == (
        "You have passed into a python enum value as the default value into "
        "of a config enum type NativeEnum. You must pass in the underlying string "
        "represention as the default value. One of ['FOO', 'BAR']."
    )


def test_native_enum_classmethod_creates_all_values():
    dagster_enum = Enum.from_python_enum(NativeEnum)
    for enum_value in NativeEnum:
        assert enum_value is dagster_enum.post_process(enum_value.name)
