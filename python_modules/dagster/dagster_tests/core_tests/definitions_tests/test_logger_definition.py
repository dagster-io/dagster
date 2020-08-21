import logging

from dagster import (
    Enum,
    EnumValue,
    Field,
    Int,
    ModeDefinition,
    configured,
    execute_pipeline,
    logger,
    pipeline,
)
from dagster.core.log_manager import coerce_valid_log_level


def assert_pipeline_runs_with_logger(logger_def, logger_config):
    @pipeline(mode_defs=[ModeDefinition(logger_defs={"test_logger": logger_def})])
    def pass_pipeline():
        pass

    # give us an opportunity to try an empty dict here
    config_value = {"config": logger_config} if logger_config else {}

    result = execute_pipeline(pass_pipeline, {"loggers": {"test_logger": config_value}})
    assert result.success


def test_dagster_type_logger_decorator_config():
    @logger(Int)
    def dagster_type_logger_config(_):
        raise Exception("not called")

    assert dagster_type_logger_config.config_schema.config_type.given_name == "Int"

    @logger(int)
    def python_type_logger_config(_):
        raise Exception("not called")

    assert python_type_logger_config.config_schema.config_type.given_name == "Int"


def test_logger_using_configured():
    it = {"ran": False}

    @logger(config_schema=Field(str))
    def test_logger(init_context):
        assert init_context.logger_config == "secret testing value!!"
        it["ran"] = True

        logger_ = logging.Logger("test", level=coerce_valid_log_level("INFO"))
        return logger_

    test_logger_configured = configured(test_logger)("secret testing value!!")

    assert_pipeline_runs_with_logger(test_logger_configured, {})
    assert it["ran"]


def test_logger_with_enum_in_schema_using_configured():
    from enum import Enum as PythonEnum

    class TestPythonEnum(PythonEnum):
        VALUE_ONE = 0
        OTHER = 1

    DagsterEnumType = Enum(
        "TestEnum",
        [
            EnumValue("VALUE_ONE", TestPythonEnum.VALUE_ONE),
            EnumValue("OTHER", TestPythonEnum.OTHER),
        ],
    )

    it = {}

    @logger(config_schema={"enum": DagsterEnumType})
    def test_logger(init_context):
        assert init_context.logger_config["enum"] == TestPythonEnum.OTHER
        it["ran test_logger"] = True

        logger_ = logging.Logger("test", level=coerce_valid_log_level("INFO"))
        return logger_

    @configured(test_logger, {"enum": DagsterEnumType})
    def pick_different_enum_value(config):
        it["ran pick_different_enum_value"] = True
        return {"enum": "OTHER" if config["enum"] == TestPythonEnum.VALUE_ONE else "VALUE_ONE"}

    assert_pipeline_runs_with_logger(pick_different_enum_value, {"enum": "VALUE_ONE"})

    assert it["ran test_logger"]
    assert it["ran pick_different_enum_value"]
