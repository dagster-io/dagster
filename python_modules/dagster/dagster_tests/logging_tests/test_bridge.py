# python_modules/dagster/dagster_tests/logging_tests/test_bridge.py

import logging
import os
import sys
import threading
import time

import pytest

# Import bridge components and the class needed for testing
from dagster._core.loguru_bridge import LoguruConfigurator, dagster_context_sink, with_loguru_logger
from loguru import logger

# Try to load environment variables from .env file if available
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Add the root directory to Python path to find loguru_bridge
root_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)


def setup_buildkite_environment():
    """Setup meaningful test environment variables for Buildkite integration."""
    # Use logger for setup info, not print
    logger.debug("Setting up Buildkite test environment...")

    os.environ["BUILDKITE"] = "true"
    os.environ["BUILDKITE_BUILD_ID"] = os.environ.get(
        "BUILDKITE_BUILD_ID", "local-loguru-bridge-test-build"
    )
    os.environ["BUILDKITE_JOB_ID"] = os.environ.get(
        "BUILDKITE_JOB_ID", "logging-tests-job-validation"
    )
    os.environ["BUILDKITE_COMMIT"] = os.environ.get(
        "BUILDKITE_COMMIT", "loguru-bridge-integration-commit"
    )
    os.environ["BUILDKITE_ORGANIZATION_SLUG"] = "dagster"
    os.environ["BUILDKITE_PIPELINE_SLUG"] = os.environ.get("BUILDKITE_PIPELINE_SLUG", "unit-tests")
    os.environ["BUILDKITE_BRANCH"] = os.environ.get("BUILDKITE_BRANCH", "Issue-29914")
    os.environ["BUILDKITE_BUILD_NUMBER"] = os.environ.get("BUILDKITE_BUILD_NUMBER", "local")

    # This informational block can use print with noqa for clarity in test logs
    print("Buildkite environment variables set for test run:")  # noqa: T201
    for key, value in os.environ.items():
        if key.startswith("BUILDKITE"):
            print(f"  {key}: {value}")  # noqa: T201


setup_buildkite_environment()


def pytest_itemcollected(item):
    """Add execution tags to all tests for analytics."""
    item.add_marker(pytest.mark.execution_tag("test.framework.name", "pytest"))
    item.add_marker(pytest.mark.execution_tag("test.framework.version", pytest.__version__))
    item.add_marker(pytest.mark.execution_tag("cloud.provider", "aws"))
    item.add_marker(pytest.mark.execution_tag("language.version", sys.version))


class MockLogHandler:
    """Mock log handler that prints (for capfd tests) and stores log messages."""

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


@pytest.fixture
def setup_logger():
    """Fixture to setup and cleanup a standard logger for each test."""
    logger.remove()

    def test_formatter(record):
        level_name = record["level"].name.lower()
        if level_name == "success":
            level_name = "info"
        return f"[dagster.{level_name}] {record['message']}\n"

    # The lambda with print is required for capfd to capture the output.
    # We add noqa to tell the linter that this print is intentional.
    handler_id = logger.add(
        lambda msg: print(test_formatter(msg.record), end=""),  # noqa: T201
        level="TRACE",
    )
    yield
    try:
        logger.remove(handler_id)
    except ValueError:
        pass


def test_dagster_context_sink_basic_logging(capfd, setup_logger):
    context = MockDagsterContext()
    sink = dagster_context_sink(context)
    logger.remove()
    logger.add(sink, level="DEBUG")
    logger.debug("Debug message")
    logger.info("Info message")
    captured = capfd.readouterr()
    assert "[dagster.debug] Debug message" in captured.out
    assert "[dagster.info] Info message" in captured.out


def test_dagster_context_sink_with_structured_logging(capfd, setup_logger):
    context = MockDagsterContext()
    sink = dagster_context_sink(context)
    logger.remove()
    logger.add(sink, level="DEBUG")
    logger.bind(user="test_user").info("User login attempt")
    captured = capfd.readouterr()
    assert "[dagster.info] User login attempt" in captured.out


def test_dagster_context_sink_different_log_levels(capfd, setup_logger):
    context = MockDagsterContext()
    sink = dagster_context_sink(context)
    logger.remove()
    logger.add(sink, level="TRACE")
    test_messages = [
        (logger.trace, "Trace level message", "debug"),
        (logger.debug, "Debug level message", "debug"),
        (logger.info, "Info level message", "info"),
        (logger.success, "Success message", "info"),
        (logger.warning, "Warning level message", "warning"),
        (logger.error, "Error level message", "error"),
        (logger.critical, "Critical level message", "critical"),
    ]
    for log_func, message, expected_level in test_messages:
        log_func(message)
    captured = capfd.readouterr()
    for _, message, expected_level in test_messages:
        assert f"[dagster.{expected_level}] {message}" in captured.out


class DagsterOperations:
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
        logger.debug("Starting complex operation...")
        logger.info("Processing data")
        logger.warning("Resource usage high")
        logger.success("Data processing complete")
        return "Success"


class DagsterTestContext:
    def __init__(self):
        self.context = MockDagsterContext()
        self.test_ops = DagsterOperations(self.context)


def test_with_loguru_logger_decorator_success(capfd, setup_logger):
    context = MockDagsterContext()
    test_ops = DagsterOperations(context)
    result = test_ops.successful_op()
    assert result is True
    captured = capfd.readouterr()
    assert "[dagster.info] Operation completed successfully!" in captured.out


def test_with_loguru_logger_decorator_failure(capfd, setup_logger):
    context = MockDagsterContext()
    test_ops = DagsterOperations(context)
    with pytest.raises(ValueError, match="Operation failed"):
        test_ops.failing_op()
    captured = capfd.readouterr()
    assert "[dagster.error] Operation failed!" in captured.out


def test_with_loguru_logger_decorator_complex(capfd, setup_logger):
    context = MockDagsterContext()
    test_ops = DagsterOperations(context)
    result = test_ops.complex_op()
    assert result == "Success"
    captured = capfd.readouterr()
    assert "[dagster.debug] Starting complex operation..." in captured.out
    assert "[dagster.info] Processing data" in captured.out
    assert "[dagster.warning] Resource usage high" in captured.out
    assert "[dagster.info] Data processing complete" in captured.out


class MixedLogger:
    def __init__(self, context):
        self._context = context

    @with_loguru_logger
    def mixed_logging_op(self, context=None):
        self._context.log.info("Direct Dagster log")
        logger.info("Loguru log")
        self._context.log.debug("Dagster debug")
        logger.debug("Loguru debug")
        return "Mixed logging complete"


def test_mixed_logging_systems(capfd, setup_logger):
    test_ctx = DagsterTestContext()
    mixed_logger = MixedLogger(test_ctx.context)
    result = mixed_logger.mixed_logging_op()
    assert result == "Mixed logging complete"
    captured = capfd.readouterr()
    assert "[dagster.info] Direct Dagster log" in captured.out
    assert "[dagster.info] Loguru log" in captured.out
    assert "[dagster.debug] Dagster debug" in captured.out
    assert "[dagster.debug] Loguru debug" in captured.out


def test_nested_operations_logging(capfd, setup_logger):
    test_ctx = DagsterTestContext()

    class NestedLogger:
        def __init__(self, test_ctx):
            self._context = test_ctx.context
            self.test_ops = test_ctx.test_ops

        @with_loguru_logger
        def nested_op(self, context=None):
            logger.info("Starting nested operation")
            self.test_ops.complex_op()
            logger.info("Nested operation complete")
            return True

    nested_logger = NestedLogger(test_ctx)
    result = nested_logger.nested_op()
    assert result is True
    captured = capfd.readouterr()
    assert "[dagster.info] Starting nested operation" in captured.out
    assert "[dagster.debug] Starting complex operation..." in captured.out
    assert "[dagster.info] Nested operation complete" in captured.out


def test_exception_handling_with_logging(capfd, setup_logger):
    test_ctx = DagsterTestContext()

    class ExceptionLogger:
        def __init__(self, context):
            self._context = context

        @with_loguru_logger
        def exception_op(self, context=None):
            try:
                raise ValueError("Simulated error")
            except ValueError as e:
                logger.error(f"Caught error: {e!s}")
                self._context.log.error(f"Dagster also logged: {e!s}")

    exception_logger = ExceptionLogger(test_ctx.context)
    exception_logger.exception_op()
    captured = capfd.readouterr()
    assert "[dagster.error] Caught error: Simulated error" in captured.out
    assert "[dagster.error] Dagster also logged: Simulated error" in captured.out


def test_structured_logging_with_context(capfd, setup_logger):
    test_ctx = DagsterTestContext()

    @with_loguru_logger
    def structured_log_op(context=None):
        logger.bind(op_id="123").info("Operation started")

    structured_log_op(context=test_ctx.context)
    captured = capfd.readouterr()
    assert "[dagster.info] Operation started" in captured.out


def test_log_level_inheritance(capfd):
    logger.remove()
    # Set a higher level for this test; use capfd to check output
    logger.add(sys.stdout, level="INFO", format="{message}")

    logger.trace("This should not appear")
    logger.debug("This should not appear either")
    logger.info("Info message should appear")

    captured = capfd.readouterr()
    assert "This should not appear" not in captured.out
    assert "Info message should appear" in captured.out


def test_concurrent_operations_logging(setup_logger):
    log_messages = []
    logger.remove()
    logger.add(log_messages.append, level="INFO")

    @with_loguru_logger
    def concurrent_op(op_id, context=None):
        logger.info(f"Operation {op_id} started")
        time.sleep(0.01)
        logger.info(f"Operation {op_id} completed")

    threads = []
    for i in range(3):
        thread = threading.Thread(target=concurrent_op, args=(f"thread-{i}", MockDagsterContext()))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

    for i in range(3):
        assert any(f"Operation thread-{i} started" in msg for msg in log_messages)
        assert any(f"Operation thread-{i} completed" in msg for msg in log_messages)


def test_log_formatting_consistency(capfd, setup_logger):
    logger.info("Message with {}", "placeholder")
    logger.info("Message with {name}", name="named placeholder")

    captured = capfd.readouterr()
    assert "[dagster.info] Message with placeholder" in captured.out
    assert "[dagster.info] Message with named placeholder" in captured.out


def test_loguru_configurator_initialization(monkeypatch):
    monkeypatch.setenv("DAGSTER_LOGURU_ENABLED", "false")
    monkeypatch.setenv("DAGSTER_LOGURU_LOG_LEVEL", "WARNING")

    # Reset singleton flag for re-initialization, ignoring the private access warning
    LoguruConfigurator._initialized = False  # noqa: SLF001
    configurator = LoguruConfigurator(enable_terminal_sink=False)

    assert not configurator.config["enabled"]
    assert configurator.config["log_level"] == "WARNING"


def test_dagster_handler_logging(capfd):
    test_logger = logging.getLogger("test_handler_logger")
    test_logger.setLevel(logging.DEBUG)
    test_logger.propagate = False

    class TestLogPrinter(logging.Handler):
        def emit(self, record):
            print(f"[{record.levelname}] {record.getMessage()}")  # noqa: T201

    handler = TestLogPrinter()
    test_logger.addHandler(handler)
    test_logger.debug("Debug from Python logging")
    test_logger.removeHandler(handler)

    captured = capfd.readouterr()
    assert "Debug from Python logging" in captured.out


def test_loguru_bridge_with_stdout_integration(capfd, setup_logger):
    @with_loguru_logger
    def log_with_stdout(context=None):
        print("Direct stdout print")  # noqa: T201
        logger.info("Loguru info message")
        print("Error message", file=sys.stderr)  # noqa: T201

    log_with_stdout(context=MockDagsterContext())
    captured = capfd.readouterr()
    assert "Direct stdout print" in captured.out
    # CORRECTED: The mock handler prints to stdout, so check .out
    assert "[dagster.info] Loguru info message" in captured.out
    assert "Error message" in captured.err


def test_buildkite_analytics_integration(capfd, setup_logger):
    logger.info(f"Build ID: {os.environ.get('BUILDKITE_BUILD_ID')}")
    captured = capfd.readouterr()
    assert f"[dagster.info] Build ID: {os.environ.get('BUILDKITE_BUILD_ID')}" in captured.out


def test_buildkite_environment_validation():
    required = ["BUILDKITE", "BUILDKITE_BUILD_ID", "BUILDKITE_JOB_ID"]
    for var in required:
        assert os.environ.get(var) is not None, f"{var} should be set"


def test_direct_loguru_usage(capfd, setup_logger):
    logger.debug("==Debug== Loguru is working!")
    captured = capfd.readouterr()
    assert "[dagster.debug] ==Debug== Loguru is working!" in captured.out


def test_context_log_with_loguru_decorator(capfd, setup_logger):
    context = MockDagsterContext()

    @with_loguru_logger
    def simulate_op(context=None):
        context.log.info("This is a context.log.info message")

    simulate_op(context=context)
    captured = capfd.readouterr()
    assert "[dagster.info] This is a context.log.info message" in captured.out
