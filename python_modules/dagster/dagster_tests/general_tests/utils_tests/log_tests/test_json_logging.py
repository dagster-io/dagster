import json
import logging

from dagster import PipelineDefinition
from dagster.core.execution.context.logger import InitLoggerContext
from dagster.utils.log import define_json_file_logger
from dagster.utils.test import create_test_pipeline_execution_context, get_temp_file_name


def setup_json_file_logger(tf_name, name="foo", level=logging.DEBUG):
    logger_def = define_json_file_logger(name, tf_name, level)
    init_logger_context = InitLoggerContext(
        {},
        logger_def,
        pipeline_def=PipelineDefinition([], "test"),
        run_id="",
    )

    return logger_def.logger_fn(init_logger_context)


def test_basic_logging():
    with get_temp_file_name() as tf_name:
        logger = setup_json_file_logger(tf_name)
        logger.debug("bar")

        data = list(parse_json_lines(tf_name))

    assert len(data) == 1
    assert data[0]["name"] == "foo"
    assert data[0]["msg"] == "bar"


def parse_json_lines(tf_name):
    with open(tf_name) as f:
        for line in f:
            yield json.loads(line)


def test_no_double_write_diff_names():
    with get_temp_file_name() as tf_name:
        foo_logger = setup_json_file_logger(tf_name)
        baaz_logger = setup_json_file_logger(tf_name, "baaz")
        foo_logger.debug("foo message")
        baaz_logger.debug("baaz message")

        data = list(parse_json_lines(tf_name))

        assert len(data) == 2
        assert data[0]["name"] == "foo"
        assert data[0]["msg"] == "foo message"
        assert data[1]["name"] == "baaz"
        assert data[1]["msg"] == "baaz message"


# This demonstrates different, less global, behavior than the typical
# python logger. Same name does *not* mean the same logger instance
# here. Hence logger one *retains* debug level while logger_two is
# a separate instance with info level
def test_no_double_write_same_names():
    with get_temp_file_name() as tf_name:
        foo_logger_one = setup_json_file_logger(tf_name)
        foo_logger_two = setup_json_file_logger(tf_name, "foo", logging.INFO)
        foo_logger_one.debug("logger one message")
        foo_logger_two.debug("logger two message")

        data = list(parse_json_lines(tf_name))
        assert len(data) == 1
        assert data[0]["name"] == "foo"
        assert data[0]["msg"] == "logger one message"


# This test ensures the behavior that the clarify project relies upon
# See extended comment in JsonFileHandler::emit
def test_write_dagster_meta():
    with get_temp_file_name() as tf_name:
        execution_context = create_test_pipeline_execution_context(
            logger_defs={"json": define_json_file_logger("foo", tf_name, logging.DEBUG)}
        )
        execution_context.log.debug("some_debug_message", context_key="context_value")
        data = list(parse_json_lines(tf_name))
        assert len(data) == 1
        assert data[0]["name"] == "foo"
        assert data[0]["orig_message"] == "some_debug_message"
        assert data[0]["context_key"] == "context_value"
