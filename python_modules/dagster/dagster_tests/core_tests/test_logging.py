import json
import logging
import re
import sys
from contextlib import contextmanager

import pytest

from dagster import (
    DagsterInvalidConfigError,
    ModeDefinition,
    PipelineRun,
    check,
    execute_pipeline,
    execute_solid,
    pipeline,
    resource,
    solid,
)
from dagster.core.definitions import NodeHandle
from dagster.core.events import DagsterEvent
from dagster.core.execution.context.logger import InitLoggerContext
from dagster.core.execution.plan.objects import StepFailureData
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.log_manager import DagsterLogManager
from dagster.core.test_utils import instance_for_test
from dagster.loggers import colored_console_logger, json_console_logger
from dagster.utils.error import SerializableErrorInfo

REGEX_UUID = r"[a-z-0-9]{8}\-[a-z-0-9]{4}\-[a-z-0-9]{4}\-[a-z-0-9]{4}\-[a-z-0-9]{12}"
REGEX_TS = r"\d{4}\-\d{2}\-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}"

DAGSTER_DEFAULT_LOGGER = "dagster"


@contextmanager
def _setup_logger(name, log_levels=None):
    """Test helper that creates a new logger.

    Args:
        name (str): The name of the logger.
        log_levels (Optional[Dict[str, int]]): Any non-standard log levels to expose on the logger
            (e.g., logger.success)
    """
    log_levels = check.opt_dict_param(log_levels, "log_levels")

    class TestLogger(logging.Logger):  # py27 compat
        pass

    logger = TestLogger(name)

    captured_results = []

    def log_fn(msg, *args, **kwargs):  # pylint:disable=unused-argument
        captured_results.append(msg)

    def int_log_fn(level, msg, *args, **kwargs):  # pylint:disable=unused-argument
        captured_results.append(msg)

    for level in ["debug", "info", "warning", "error", "critical"] + list(
        [x.lower() for x in log_levels.keys()]
    ):
        setattr(logger, level, log_fn)
        setattr(logger, "log", int_log_fn)

    yield (captured_results, logger)


def test_logging_no_loggers_registered():
    dl = DagsterLogManager.create(loggers=[])
    dl.debug("test")
    dl.info("test")
    dl.warning("test")
    dl.error("test")
    dl.critical("test")


def test_logging_basic():
    with _setup_logger("test") as (captured_results, logger):

        dl = DagsterLogManager.create(
            loggers=[logger], pipeline_run=PipelineRun(pipeline_name="system", run_id="123")
        )
        dl.debug("test")
        dl.info("test")
        dl.warning("test")
        dl.error("test")
        dl.critical("test")

        assert captured_results == ["system - 123 - test"] * 5


def test_logging_custom_log_levels():
    with _setup_logger("test", {"FOO": 3}) as (_captured_results, logger):

        dl = DagsterLogManager.create(
            loggers=[logger], pipeline_run=PipelineRun(pipeline_name="system", run_id="123")
        )
        with pytest.raises(AttributeError):
            dl.foo("test")  # pylint: disable=no-member


def test_logging_integer_log_levels():
    with _setup_logger("test", {"FOO": 3}) as (_captured_results, logger):

        dl = DagsterLogManager.create(
            loggers=[logger], pipeline_run=PipelineRun(pipeline_name="system", run_id="123")
        )
        dl.log(3, "test")  # pylint: disable=no-member


def test_logging_bad_custom_log_levels():
    with _setup_logger("test") as (_, logger):

        dl = DagsterLogManager.create(
            loggers=[logger], pipeline_run=PipelineRun(pipeline_name="system", run_id="123")
        )
        with pytest.raises(check.CheckError):
            dl.log(level="test", msg="foobar")


def test_multiline_logging_complex():
    msg = "DagsterEventType.STEP_FAILURE for step start.materialization.output.result.0"
    dagster_event = DagsterEvent(
        event_type_value="STEP_FAILURE",
        pipeline_name="error_monster",
        step_key="start.materialization.output.result.0",
        solid_handle=NodeHandle("start", None),
        step_kind_value="MATERIALIZATION_THUNK",
        logging_tags={
            "pipeline": "error_monster",
            "step_key": "start.materialization.output.result.0",
            "solid": "start",
            "solid_definition": "emit_num",
        },
        event_specific_data=StepFailureData(
            error=SerializableErrorInfo(
                message="FileNotFoundError: [Errno 2] No such file or directory: '/path/to/file'\n",
                stack=["a stack message"],
                cls_name="FileNotFoundError",
            ),
            user_failure_data=None,
        ),
    )

    with _setup_logger(DAGSTER_DEFAULT_LOGGER) as (captured_results, logger):

        dl = DagsterLogManager.create(
            loggers=[logger], pipeline_run=PipelineRun(run_id="123", pipeline_name="error_monster")
        )
        dl.log_dagster_event(logging.INFO, msg, dagster_event)

    expected_results = [
        "error_monster - 123 - STEP_FAILURE - DagsterEventType.STEP_FAILURE for step "
        "start.materialization.output.result.0",
        "",
        "FileNotFoundError: [Errno 2] No such file or directory: '/path/to/file'",
        "",
        "Stack Trace:",
        "a stack message",
    ]

    assert captured_results[0].split("\n") == expected_results


def _setup_test_two_handler_log_mgr():
    test_formatter = logging.Formatter(fmt="%(levelname)s :: %(message)s")

    test_info_handler = logging.StreamHandler(sys.stdout)
    test_info_handler.setLevel("INFO")
    test_info_handler.setFormatter(test_formatter)

    test_warn_handler = logging.StreamHandler(sys.stdout)
    test_warn_handler.setLevel("WARN")
    test_warn_handler.setFormatter(test_formatter)

    return DagsterLogManager.create(
        loggers=[],
        handlers=[test_info_handler, test_warn_handler],
        pipeline_run=PipelineRun(pipeline_name="system", run_id="123"),
    )


def test_handler_in_log_manager(capsys):
    dl = _setup_test_two_handler_log_mgr()

    dl.info("test")
    dl.warning("test")

    out, _ = capsys.readouterr()

    assert re.search(r"INFO :: system - 123 - test", out)
    assert len(re.findall(r"WARNING :: system - 123 - test", out)) == 2


def test_handler_in_log_manager_with_tags(capsys):
    dl = _setup_test_two_handler_log_mgr()
    dl = dl.with_tags(**{"pipeline_name": "test_pipeline"})

    dl.info("test")
    dl.warning("test")

    out, _ = capsys.readouterr()

    assert re.search(r"INFO :: test_pipeline - 123 - test", out)
    assert len(re.findall(r"WARNING :: test_pipeline - 123 - test", out)) == 2


class CaptureHandler(logging.Handler):
    def __init__(self, output=None):
        self.captured = []
        self.output = output
        super().__init__(logging.INFO)

    def emit(self, record):
        if self.output:
            print(self.output + record.msg)  # pylint: disable=print-call
        self.captured.append(record)


def test_capture_handler_log_records():
    capture_handler = CaptureHandler()

    dl = DagsterLogManager.create(
        loggers=[],
        handlers=[capture_handler],
        pipeline_run=PipelineRun(run_id="123456", pipeline_name="pipeline"),
    ).with_tags(step_key="some_step")

    dl.info("info")
    dl.critical("critical error", extra={"foo": "bar"})

    assert len(capture_handler.captured) == 2

    captured_info_record = capture_handler.captured[0]
    assert captured_info_record.name == "dagster"
    assert captured_info_record.msg == "pipeline - 123456 - some_step - info"
    assert captured_info_record.levelno == logging.INFO

    captured_critical_record = capture_handler.captured[1]
    assert captured_critical_record.name == "dagster"
    assert captured_critical_record.msg == "pipeline - 123456 - some_step - critical error"
    assert captured_critical_record.levelno == logging.CRITICAL
    assert captured_critical_record.foo == "bar"


def test_default_context_logging():
    called = {}

    @solid(input_defs=[], output_defs=[])
    def default_context_solid(context):
        called["yes"] = True
        for logger in context.log._dagster_handler._loggers:  # pylint: disable=protected-access
            assert logger.level == logging.DEBUG

    execute_solid(default_context_solid)

    assert called["yes"]


def test_colored_console_logger_with_integer_log_level():
    @pipeline
    def pipe():
        pass

    colored_console_logger.logger_fn(
        InitLoggerContext(
            {"name": "dagster", "log_level": 4},
            colored_console_logger,
            pipeline_def=pipe,
        )
    )


def test_json_console_logger(capsys):
    @solid
    def hello_world(context):
        context.log.info("Hello, world!")

    execute_solid(
        hello_world,
        mode_def=ModeDefinition(logger_defs={"json": json_console_logger}),
        run_config={"loggers": {"json": {"config": {}}}},
    )

    captured = capsys.readouterr()

    found_msg = False
    for line in captured.err.split("\n"):
        if line:
            parsed = json.loads(line)
            if parsed["dagster_meta"]["orig_message"] == "Hello, world!":
                found_msg = True

    assert found_msg


def test_pipeline_logging(capsys):
    @solid
    def foo(context):
        context.log.info("bar")
        return 0

    @solid
    def foo2(context, _in1):
        context.log.info("baz")

    @pipeline
    def pipe():
        foo2(foo())

    execute_pipeline(pipe)

    captured = capsys.readouterr()
    expected_log_regexes = [
        r"dagster - INFO - pipe - [a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-"
        r"[a-f0-9]{12} - foo - bar",
        r"dagster - INFO - pipe - [a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-"
        r"[a-f0-9]{12} - foo2 - baz",
    ]
    for expected_log_regex in expected_log_regexes:
        assert re.search(expected_log_regex, captured.err, re.MULTILINE)


def test_resource_logging(capsys):
    @resource
    def foo_resource(init_context):
        def fn():
            init_context.log.info("test logging from foo resource")

        return fn

    @resource
    def bar_resource(init_context):
        def fn():
            init_context.log.info("test logging from bar resource")

        return fn

    @solid(required_resource_keys={"foo", "bar"})
    def process(context):
        context.resources.foo()
        context.resources.bar()

    execute_solid(
        process,
        mode_def=ModeDefinition(resource_defs={"foo": foo_resource, "bar": bar_resource}),
    )

    captured = capsys.readouterr()

    expected_log_regexes = [
        r"dagster - INFO - resource:foo - [a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-"
        r"[a-f0-9]{12} - process - test logging from foo resource",
        r"dagster - INFO - resource:bar - [a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-"
        r"[a-f0-9]{12} - process - test logging from bar resource",
    ]
    for expected_log_regex in expected_log_regexes:
        assert re.search(expected_log_regex, captured.err, re.MULTILINE)


def test_io_context_logging(capsys):
    @solid
    def logged_solid(context):
        context.get_step_execution_context().get_output_context(
            StepOutputHandle("logged_solid", "result")
        ).log.debug("test OUTPUT debug logging from logged_solid.")
        context.get_step_execution_context().for_input_manager(
            "logged_solid", {}, {}, None, source_handle=None
        ).log.debug("test INPUT debug logging from logged_solid.")

    result = execute_solid(logged_solid)
    assert result.success

    captured = capsys.readouterr()

    assert re.search("test OUTPUT debug logging from logged_solid.", captured.err, re.MULTILINE)
    assert re.search("test INPUT debug logging from logged_solid.", captured.err, re.MULTILINE)


@solid
def log_solid(context):
    context.log.info("Hello world")
    context.log.error("My test error")


@pipeline
def log_pipeline():
    log_solid()


def test_conf_file_logging(capsys):
    config_settings = {
        "python_logs": {
            "dagster_handler_config": {
                "handlers": {
                    "handlerOne": {
                        "class": "logging.StreamHandler",
                        "level": "INFO",
                        "stream": "ext://sys.stdout",
                    },
                    "handlerTwo": {
                        "class": "logging.StreamHandler",
                        "level": "ERROR",
                        "stream": "ext://sys.stdout",
                    },
                },
            }
        }
    }

    with instance_for_test(overrides=config_settings) as instance:
        execute_pipeline(log_pipeline, instance=instance)

    out, _ = capsys.readouterr()

    # currently the format of dict-inputted handlers is undetermined, so
    # we only check for the expected message
    assert re.search(r"Hello world", out)
    assert len(re.findall(r"My test error", out)) == 2


def test_custom_class_handler(capsys):
    output_msg = "Record handled: "
    config_settings = {
        "python_logs": {
            "dagster_handler_config": {
                "handlers": {
                    "handlerOne": {
                        "()": "dagster_tests.core_tests.test_logging.CaptureHandler",
                        "level": "INFO",
                        "output": output_msg,
                    }
                },
            },
        }
    }

    with instance_for_test(overrides=config_settings) as instance:
        execute_pipeline(log_pipeline, instance=instance)

    out, _ = capsys.readouterr()

    assert re.search(r".*Record handled: .*Hello world.*", out)


def test_error_when_logger_defined_yaml():
    config_settings = {
        "python_logs": {
            "dagster_handler_config": {
                "loggers": {
                    "my_logger": {"level": "WARNING", "propagate": False},
                },
            },
        }
    }

    with pytest.raises(DagsterInvalidConfigError):
        with instance_for_test(overrides=config_settings) as instance:
            execute_pipeline(log_pipeline, instance=instance)


def test_python_log_level_context_logging():
    @solid
    def logged_solid(context):
        context.log.error("some error")

    @pipeline
    def pipe():
        logged_solid()

    with instance_for_test() as instance:
        result = execute_pipeline(pipe, instance=instance)
        logs_default = instance.event_log_storage.get_logs_for_run(result.run_id)

    with instance_for_test(overrides={"python_logs": {"python_log_level": "CRITICAL"}}) as instance:
        result = execute_pipeline(pipe, instance=instance)
        logs_critical = instance.event_log_storage.get_logs_for_run(result.run_id)

    assert len(logs_critical) > 0  # DagsterEvents should still be logged
    assert len(logs_default) == len(logs_critical) + 1
