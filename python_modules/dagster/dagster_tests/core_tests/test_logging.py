import json
import logging
import re
from contextlib import contextmanager

import pytest
from dagster import ModeDefinition, check, execute_solid, pipeline, resource, solid
from dagster.core.definitions import SolidHandle
from dagster.core.events import DagsterEvent
from dagster.core.execution.context.logger import InitLoggerContext
from dagster.core.execution.plan.objects import StepFailureData
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.log_manager import DagsterLogManager
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

    def int_log_fn(lvl, msg, *args, **kwargs):  # pylint:disable=unused-argument
        captured_results.append(msg)

    for level in ["debug", "info", "warning", "error", "critical"] + list(
        [x.lower() for x in log_levels.keys()]
    ):
        setattr(logger, level, log_fn)
        setattr(logger, "log", int_log_fn)

    yield (captured_results, logger)


def _regex_match_kv_pair(regex, kv_pairs):
    return any([re.match(regex, kv_pair) for kv_pair in kv_pairs])


def test_logging_no_loggers_registered():
    dl = DagsterLogManager("none", {}, [])
    dl.debug("test")
    dl.info("test")
    dl.warning("test")
    dl.error("test")
    dl.critical("test")


def test_logging_basic():
    with _setup_logger("test") as (captured_results, logger):

        dl = DagsterLogManager("123", {}, [logger])
        dl.debug("test")
        dl.info("test")
        dl.warning("test")
        dl.error("test")
        dl.critical("test")

        assert captured_results == ["system - 123 - test"] * 5


def test_logging_custom_log_levels():
    with _setup_logger("test", {"FOO": 3}) as (_captured_results, logger):

        dl = DagsterLogManager("123", {}, [logger])
        with pytest.raises(AttributeError):
            dl.foo("test")  # pylint: disable=no-member


def test_logging_integer_log_levels():
    with _setup_logger("test", {"FOO": 3}) as (_captured_results, logger):

        dl = DagsterLogManager("123", {}, [logger])
        dl.log(3, "test")  # pylint: disable=no-member


def test_logging_bad_custom_log_levels():
    with _setup_logger("test") as (_, logger):

        dl = DagsterLogManager("123", {}, [logger])
        with pytest.raises(check.CheckError):
            dl._log("test", "foobar", {})  # pylint: disable=protected-access


def test_multiline_logging_complex():
    msg = "DagsterEventType.STEP_FAILURE for step start.materialization.output.result.0"
    kwargs = {
        "pipeline": "example",
        "pipeline_name": "error_monster",
        "step_key": "start.materialization.output.result.0",
        "solid": "start",
        "solid_definition": "emit_num",
        "dagster_event": DagsterEvent(
            event_type_value="STEP_FAILURE",
            pipeline_name="error_monster",
            step_key="start.materialization.output.result.0",
            solid_handle=SolidHandle("start", None),
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
        ),
    }

    with _setup_logger(DAGSTER_DEFAULT_LOGGER) as (captured_results, logger):

        dl = DagsterLogManager("123", {}, [logger])
        dl.info(msg, **kwargs)

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


def test_default_context_logging():
    called = {}

    @solid(input_defs=[], output_defs=[])
    def default_context_solid(context):
        called["yes"] = True
        for logger in context.log.loggers:
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


def test_resource_logging(capsys):
    @resource
    def foo_resource(init_context):
        def fn():
            init_context.log_manager.info("test logging from foo resource")

        return fn

    @resource
    def bar_resource(init_context):
        def fn():
            init_context.log_manager.info("test logging from bar resource")

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
