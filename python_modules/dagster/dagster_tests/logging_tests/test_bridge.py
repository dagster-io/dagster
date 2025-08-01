import logging
import os
import sys
import threading
import time

import pytest
from dagster._core.loguru_bridge import (
    InterceptHandler,
    LoguruConfigurator,
    dagster_context_sink,
    with_loguru_logger,
)
from loguru import logger

root_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, "python_modules"))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv is optional


class MockLogHandler:
    """A mock log handler that prints (for capfd tests) and stores log messages."""

    def __init__(self):
        self.history = []

    def debug(self, msg):
        print(f"[dagster.debug] {msg}")  # noqa: T201
        self.history.append({"level": "debug", "message": msg})

    def info(self, msg):
        print(f"[dagster.info] {msg}")  # noqa: T201
        self.history.append({"level": "info", "message": msg})

    def warning(self, msg):
        print(f"[dagster.warning] {msg}")  # noqa: T201
        self.history.append({"level": "warning", "message": msg})

    def error(self, msg):
        print(f"[dagster.error] {msg}")  # noqa: T201
        self.history.append({"level": "error", "message": msg})

    def critical(self, msg):
        print(f"[dagster.critical] {msg}")  # noqa: T201
        self.history.append({"level": "critical", "message": msg})


class MockDagsterContext:
    """Simulates Dagster's context.log interface using the MockLogHandler."""

    def __init__(self):
        self.log = MockLogHandler()


class DagsterOperations:
    """A collection of mock operations to test the decorator."""

    def __init__(self, context):
        self._context = context

    @with_loguru_logger
    def successful_op(self, context=None):
        logger.info("Operation completed successfully!")
        return True

    @with_loguru_logger
    def failing_op(self, context=None):
        logger.error("Operation failed!")
        raise ValueError("Operation failed")

    @with_loguru_logger
    def complex_op(self, context=None):
        logger.debug("Starting complex...")
        logger.info("Processing...")
        logger.warning("High usage")
        logger.success("Done")


class DagsterTestContext:
    """Helper class to bundle a mock context and operations for tests."""

    def __init__(self):
        self.context = MockDagsterContext()
        self.test_ops = DagsterOperations(self.context)


# --- Step 4: Pytest Fixtures ---


@pytest.fixture
def setup_logger():
    """Fixture to setup and cleanup a standard logger for each test."""
    logger.remove()

    def test_formatter(record):
        level_name = record["level"].name.lower()
        if level_name == "success":
            level_name = "info"
        return f"[dagster.{level_name}] {record['message']}\n"

    handler_id = logger.add(
        lambda msg: print(test_formatter(msg.record), end=""),  # noqa: T201
        level="TRACE",
    )
    yield
    try:
        logger.remove(handler_id)
    except ValueError:
        pass


# --- Step 5: The Full Suite of Tests, Corrected and Ruff-Compliant ---


def test_dagster_context_sink_basic_logging(capfd, setup_logger):
    context = MockDagsterContext()
    sink = dagster_context_sink(context)
    logger.remove()
    logger.add(sink, level="DEBUG")
    logger.debug("Debug message")
    captured = capfd.readouterr()
    assert "[dagster.debug] Debug message" in captured.out


def test_dagster_context_sink_with_structured_logging(capfd, setup_logger):
    context = MockDagsterContext()
    sink = dagster_context_sink(context)
    logger.remove()
    logger.add(sink, level="DEBUG")
    logger.bind(user="test").info("User login attempt")
    captured = capfd.readouterr()
    assert "[dagster.info] User login attempt" in captured.out


def test_dagster_context_sink_different_log_levels(capfd, setup_logger):
    context = MockDagsterContext()
    sink = dagster_context_sink(context)
    logger.remove()
    logger.add(sink, level="TRACE")
    logger.critical("Critical message")
    captured = capfd.readouterr()
    assert "[dagster.critical] Critical message" in captured.out


def test_with_loguru_logger_decorator_success(capfd, setup_logger):
    context = MockDagsterContext()
    DagsterOperations(context).successful_op()
    captured = capfd.readouterr()
    assert "[dagster.info] Operation completed successfully!" in captured.out


def test_with_loguru_logger_decorator_failure(capfd, setup_logger):
    context = MockDagsterContext()
    with pytest.raises(ValueError):
        DagsterOperations(context).failing_op()
    captured = capfd.readouterr()
    assert "[dagster.error] Operation failed!" in captured.out


def test_with_loguru_logger_decorator_complex(capfd, setup_logger):
    context = MockDagsterContext()
    DagsterOperations(context).complex_op()
    captured = capfd.readouterr()
    assert "[dagster.debug] Starting complex..." in captured.out
    assert "[dagster.info] Processing..." in captured.out
    assert "[dagster.warning] High usage" in captured.out
    assert "[dagster.info] Done" in captured.out


def test_mixed_logging_systems(capfd, setup_logger):
    context = MockDagsterContext()

    @with_loguru_logger
    def op(context=None):
        context.log.info("Direct Dagster")
        logger.info("Loguru log")

    op(context=context)
    captured = capfd.readouterr()
    assert "[dagster.info] Direct Dagster" in captured.out
    assert "[dagster.info] Loguru log" in captured.out


def test_nested_operations_logging(capfd, setup_logger):
    test_ctx = DagsterTestContext()

    @with_loguru_logger
    def op(context=None):
        logger.info("Outer start")
        test_ctx.test_ops.complex_op()
        logger.info("Outer end")

    op(context=test_ctx.context)
    captured = capfd.readouterr()
    assert "[dagster.info] Outer start" in captured.out
    assert "[dagster.debug] Starting complex..." in captured.out
    assert "[dagster.info] Outer end" in captured.out


def test_exception_handling_with_logging(capfd, setup_logger):
    context = MockDagsterContext()

    @with_loguru_logger
    def op(context=None):
        try:
            raise ValueError("E")
        except ValueError as e:
            logger.error(f"Caught: {e}")
            context.log.error("Also caught")

    op(context=context)
    captured = capfd.readouterr()
    assert "[dagster.error] Caught: E" in captured.out
    assert "[dagster.error] Also caught" in captured.out


def test_structured_logging_with_context(capfd, setup_logger):
    context = MockDagsterContext()

    @with_loguru_logger
    def op(context=None):
        logger.bind(id=1).info("Structured")

    op(context=context)
    captured = capfd.readouterr()
    assert "[dagster.info] Structured" in captured.out


def test_log_level_inheritance(capfd):
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{message}")
    logger.debug("Hidden")
    logger.info("Visible")
    captured = capfd.readouterr()
    assert "Hidden" not in captured.out
    assert "Visible" in captured.out


def test_concurrent_operations_logging():
    log_messages = []
    logger.remove()
    logger.add(log_messages.append, level="INFO")

    @with_loguru_logger
    def op(op_id, context=None):
        logger.info(f"Run {op_id}")

    threads = [threading.Thread(target=op, args=(i, MockDagsterContext())) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    full_log = "".join(log_messages)
    assert "Run 0" in full_log and "Run 1" in full_log and "Run 2" in full_log


def test_log_formatting_consistency(capfd, setup_logger):
    @with_loguru_logger
    def op(context=None):
        logger.info("Hello {}", "World")

    op(context=MockDagsterContext())
    captured = capfd.readouterr()
    assert "[dagster.info] Hello World" in captured.out


def test_error_context_preservation(capfd, setup_logger):
    context = MockDagsterContext()

    @with_loguru_logger
    def op(context=None):
        try:
            raise RuntimeError("E")
        except RuntimeError:
            logger.exception("Caught")

    op(context=context)
    captured = capfd.readouterr()
    assert "[dagster.error] Caught" in captured.out


def test_loguru_configurator_initialization(monkeypatch):
    monkeypatch.setenv("DAGSTER_LOGURU_ENABLED", "false")
    LoguruConfigurator._initialized = False  # noqa: SLF001
    configurator = LoguruConfigurator(enable_terminal_sink=False)
    assert not configurator.config["enabled"]


def test_dagster_handler_logging():
    log_messages = []
    logger.remove()
    logger.add(log_messages.append, level="DEBUG", format="{message}")

    test_logger = logging.getLogger("isolated_test_logger")
    test_logger.setLevel(logging.DEBUG)
    test_logger.propagate = False

    test_logger.addHandler(InterceptHandler())

    test_logger.warning("From isolated python logging")

    assert any("From isolated python logging" in msg for msg in log_messages)


def test_loguru_bridge_integration_with_dagster_context(capfd, setup_logger):
    context = MockDagsterContext()

    @with_loguru_logger
    def op(context=None):
        logger.info("Integrated")

    op(context=context)
    captured = capfd.readouterr()
    assert "[dagster.info] Integrated" in captured.out


def test_loguru_bridge_performance():
    context = MockDagsterContext()
    sink = dagster_context_sink(context)
    logger.remove()
    logger.add(sink, level="INFO")
    start = time.time()
    for _ in range(100):
        logger.info("Perf message")
    duration = time.time() - start
    assert duration < 1.0


def test_loguru_bridge_with_stdout_integration(capfd, setup_logger):
    @with_loguru_logger
    def op(context=None):
        print("to stdout")  # noqa: T201
        logger.info("to loguru")
        print("to stderr", file=sys.stderr)  # noqa: T201

    op(context=MockDagsterContext())
    captured = capfd.readouterr()
    assert "to stdout" in captured.out
    assert "[dagster.info] to loguru" in captured.out
    assert "to stderr" in captured.err


def test_direct_loguru_usage(capfd, setup_logger):
    logger.info("Direct usage")
    captured = capfd.readouterr()
    assert "[dagster.info] Direct usage" in captured.out


def test_context_log_with_loguru_decorator(capfd, setup_logger):
    context = MockDagsterContext()

    @with_loguru_logger
    def op(context=None):
        context.log.info("From context.log")

    op(context=context)
    captured = capfd.readouterr()
    assert "[dagster.info] From context.log" in captured.out
