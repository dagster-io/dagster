import logging

import dagster as dg
from dagster._core.utils import coerce_valid_log_level


def assert_job_runs_with_logger(logger_def, logger_config):
    @dg.job(logger_defs={"test_logger": logger_def})
    def pass_job():
        pass

    # give us an opportunity to try an empty dict here
    config_value = {"config": logger_config} if logger_config else {}

    assert pass_job.execute_in_process(
        run_config={"loggers": {"test_logger": config_value}}
    ).success


def test_dagster_type_logger_decorator_config():
    @dg.logger(dg.Int)
    def dagster_type_logger_config(_):
        raise Exception("not called")

    assert dagster_type_logger_config.config_schema.config_type.given_name == "Int"

    @dg.logger(int)
    def python_type_logger_config(_):
        raise Exception("not called")

    assert python_type_logger_config.config_schema.config_type.given_name == "Int"


def test_logger_using_configured():
    it = {"ran": False}

    @dg.logger(config_schema=dg.Field(str))
    def test_logger(init_context):
        assert init_context.logger_config == "secret testing value!!"
        it["ran"] = True

        logger_ = logging.Logger("test", level=coerce_valid_log_level("INFO"))
        return logger_

    test_logger_configured = dg.configured(test_logger)("secret testing value!!")

    assert_job_runs_with_logger(test_logger_configured, {})
    assert it["ran"]


def test_logger_with_enum_in_schema_using_configured():
    from enum import Enum as PythonEnum

    class TestPythonEnum(PythonEnum):
        VALUE_ONE = 0
        OTHER = 1

    DagsterEnumType = dg.Enum(
        "LoggerTestEnum",
        [
            dg.EnumValue("VALUE_ONE", TestPythonEnum.VALUE_ONE),
            dg.EnumValue("OTHER", TestPythonEnum.OTHER),
        ],
    )

    it = {}

    @dg.logger(config_schema={"enum": DagsterEnumType})
    def test_logger(init_context):
        assert init_context.logger_config["enum"] == TestPythonEnum.OTHER
        it["ran test_logger"] = True

        logger_ = logging.Logger("test", level=coerce_valid_log_level("INFO"))
        return logger_

    @dg.configured(test_logger, {"enum": DagsterEnumType})
    def pick_different_enum_value(config):
        it["ran pick_different_enum_value"] = True
        return {"enum": "OTHER" if config["enum"] == TestPythonEnum.VALUE_ONE else "VALUE_ONE"}

    assert_job_runs_with_logger(pick_different_enum_value, {"enum": "VALUE_ONE"})

    assert it["ran test_logger"]
    assert it["ran pick_different_enum_value"]
