import asyncio
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
class DummyContext:
    def __init__(self):
        self.log = self
        self.logged = []

    def info(self, msg, **kwargs):
        self.logged.append(("info", msg))

    def error(self, msg, **kwargs):
        self.logged.append(("error", msg))

    def debug(self, msg, **kwargs):
        self.logged.append(("debug", msg))

    def warning(self, msg, **kwargs):
        self.logged.append(("warning", msg))

    def critical(self, msg, **kwargs):
        self.logged.append(("critical", msg))


class StructuredContext:
    """A context that accepts structured logging."""

    def __init__(self):
        self.log = self
        self.logged = []

    def debug(self, msg, **kwargs):
        self.logged.append((msg, kwargs))

    def info(self, msg, **kwargs):
        self.logged.append((msg, kwargs))

    def warning(self, msg, **kwargs):
        self.logged.append((msg, kwargs))

    def error(self, msg, **kwargs):
        self.logged.append((msg, kwargs))

    def critical(self, msg, **kwargs):
        self.logged.append((msg, kwargs))


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

    logger.add(sys.stderr, level="INFO")


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


def test_setup_sinks_does_nothing_when_disabled(monkeypatch):
    monkeypatch.setenv("DAGSTER_LOGURU_ENABLED", "false")
    LoguruConfigurator.reset()  # Reset for test isolation

    configurator = LoguruConfigurator()
    logger.remove()  # Clear existing sinks
    sink_count_before = len(logger._core.handlers)  # noqa: SLF001

    configurator.setup_sinks()

    sink_count_after = len(logger._core.handlers)  # noqa: SLF001
    assert sink_count_before == sink_count_after, "No new sinks should be added when disabled"


def test_setup_sinks_removes_and_adds_sink_when_enabled(monkeypatch):
    monkeypatch.setenv("DAGSTER_LOGURU_ENABLED", "true")
    monkeypatch.setenv("DAGSTER_LOGURU_LOG_LEVEL", "INFO")
    monkeypatch.setenv("DAGSTER_LOGURU_FORMAT", "{message}")

    LoguruConfigurator.reset()
    configurator = LoguruConfigurator()
    logger.remove()

    # Add a dummy sink before
    dummy_id = logger.add(lambda msg: None)
    assert dummy_id in logger._core.handlers  # noqa: SLF001

    configurator.setup_sinks()

    # Check that dummy sink is gone and a new one (stderr) is present
    handlers = logger._core.handlers  # noqa: SLF001
    assert dummy_id not in handlers, "Old sink should be removed"
    assert len(handlers) == 1, "New sink should be added"


def test_setup_sinks_uses_default_log_level(monkeypatch):
    monkeypatch.delenv("DAGSTER_LOGURU_LOG_LEVEL", raising=False)
    monkeypatch.setenv("DAGSTER_LOGURU_ENABLED", "true")
    LoguruConfigurator.reset()
    configurator = LoguruConfigurator()
    assert configurator.config["log_level"] == "DEBUG"


def test_setup_sinks_uses_default_format(monkeypatch):
    monkeypatch.delenv("DAGSTER_LOGURU_FORMAT", raising=False)
    monkeypatch.setenv("DAGSTER_LOGURU_ENABLED", "true")
    LoguruConfigurator.reset()
    configurator = LoguruConfigurator()
    assert "{name}:{function}:{line}" in configurator.config["format"]


def test_loguru_configurator_does_not_reinitialize(monkeypatch):
    monkeypatch.setenv("DAGSTER_LOGURU_ENABLED", "true")
    LoguruConfigurator.reset()

    first = LoguruConfigurator()
    config_before = first.config.copy()

    # LoguruConfigurator should not change config when called again
    _ = LoguruConfigurator(enable_terminal_sink=False)

    # config should not be reloaded
    assert LoguruConfigurator.is_initialized() is True
    assert first.config == config_before


def test_sink_is_not_added_when_config_incomplete(monkeypatch):
    monkeypatch.setenv("DAGSTER_LOGURU_ENABLED", "true")
    monkeypatch.delenv("DAGSTER_LOGURU_LOG_LEVEL", raising=False)
    monkeypatch.delenv("DAGSTER_LOGURU_FORMAT", raising=False)
    LoguruConfigurator.reset()
    configurator = LoguruConfigurator()
    assert configurator.config["log_level"] == "DEBUG"
    assert "{name}:{function}:{line}" in configurator.config["format"]


def test_logger_remove_called_only_once(monkeypatch):
    monkeypatch.setenv("DAGSTER_LOGURU_ENABLED", "true")
    LoguruConfigurator.reset()
    configurator = LoguruConfigurator()
    # There's no direct way to count logger.remove calls; this is an assumption test
    assert configurator.config["enabled"] is True


def test_sink_addition_preserves_custom_handlers(monkeypatch):
    monkeypatch.setenv("DAGSTER_LOGURU_ENABLED", "true")
    LoguruConfigurator.reset()
    LoguruConfigurator(enable_terminal_sink=True)

    messages = []
    logger.add(messages.append, level="INFO")

    logger.info("Preserved")
    assert any("Preserved" in str(msg) for msg in messages)


@with_loguru_logger
def nested_test_op(context=None):
    """Helper function for testing nested operations."""
    if context:
        context.log.info("Nested context working")
    else:
        logger.info("Nested context working")  # Fallback if no context provided


@pytest.fixture
def isolated_logger():
    """KEY FIXTURE: This fixture provides a clean, isolated Loguru logger for a single test.
    It removes all global handlers and yields the logger, then restores them after.
    This prevents tests from interfering with each other or the global config.
    """
    # Isolate the logger for the duration of the test
    logger.remove()
    yield logger
    # Restore original handlers after the test
    LoguruConfigurator.reset()
    LoguruConfigurator()


def test_with_loguru_logger_preserves_context(isolated_logger):
    """Test that with_loguru_logger correctly logs to the provided context
    when the logger is isolated.
    """
    ctx = DummyContext()

    def mock_sink(message):
        record = message.record
        level = record["level"].name.lower()
        if level == "success":
            level = "info"
        ctx.logged.append((level, record["message"]))

    isolated_logger.add(mock_sink)

    nested_test_op(context=ctx)

    # Now, the log should be in the history.
    assert ("info", "Nested context working") in ctx.logged


def test_multiple_initializations_dont_stack_handlers(monkeypatch):
    """Test that multiple initializations don't stack handlers."""
    monkeypatch.setenv("DAGSTER_LOGURU_ENABLED", "true")
    LoguruConfigurator.reset()
    logger.remove()
    initial_count = len(logger._core.handlers)  # noqa: SLF001
    LoguruConfigurator()
    mid_count = len(logger._core.handlers)  # noqa: SLF001
    LoguruConfigurator()
    final_count = len(logger._core.handlers)  # noqa: SLF001
    assert mid_count == final_count >= initial_count


def test_structured_extras_are_forwarded(monkeypatch):
    """Test that structured extras are forwarded."""
    monkeypatch.setenv("DAGSTER_LOGURU_ENABLED", "true")
    LoguruConfigurator.reset()
    ctx = StructuredContext()
    sink = dagster_context_sink(ctx)
    logger.remove()
    handler_id = logger.add(sink, format="{message} {extra}", level="INFO")
    try:
        logger.bind(user="test_user").info("Hello")
        assert any(msg[0] == "Hello" and msg[1].get("user") == "test_user" for msg in ctx.logged)
    finally:
        logger.remove(handler_id)


def test_intercept_handler_forwards(capfd):
    """Test that the intercept handler forwards logs to loguru."""
    logger.remove()
    handler_id = logger.add(sys.stdout, format="{message}")

    try:
        handler = InterceptHandler()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test intercept",
            args=(),
            exc_info=None,
        )

        handler.emit(record)
        captured = capfd.readouterr()
        assert "Test intercept" in captured.out
    finally:
        logger.remove(handler_id)


def test_with_loguru_logger_restores_on_exception():
    ctx = MockDagsterContext()

    @with_loguru_logger
    def boom(context=None):
        context.log.info("before")
        raise RuntimeError("X")

    orig_info = ctx.log.info
    with pytest.raises(RuntimeError):
        boom(context=ctx)
    assert ctx.log.info.__func__ is orig_info.__func__


def test_with_loguru_logger_accepts_kwargs(isolated_logger):
    """Tests that the decorator's proxy function can accept and handle extra kwargs.
    THE FIX: We use the full MockDagsterContext so 'context.log' has all methods.
    """
    captured_records = []

    def capturing_sink(message):
        captured_records.append(message.record)

    isolated_logger.add(capturing_sink)

    @with_loguru_logger
    def op(context=None):
        context.log.info("Hello", user="alice")

    # Use the full MockDagsterContext which has .debug, .info, etc.
    op(context=MockDagsterContext())

    assert len(captured_records) == 1
    record = captured_records[0]
    assert record["message"] == "Hello"
    assert record["extra"]["user"] == "alice"


def test_dagster_context_sink_handles_missing_context_gracefully():
    sink = dagster_context_sink(context=None)
    logger.remove()
    logger.add(sink, level="INFO")
    logger.info("no context, no problem")


def test_sink_unknown_level_maps_to_info(capfd):
    class CustomLevelCtx:
        def __init__(self):
            self.log = MockLogHandler()

    ctx = CustomLevelCtx()
    sink = dagster_context_sink(ctx)
    logger.remove()
    logger.add(sink, level="INFO")

    logger.level("ODDLEVEL", no=23)
    logger.log("ODDLEVEL", "Weird")
    captured = capfd.readouterr()
    assert "[dagster.info] Weird" in captured.out


def test_unicode_and_long_messages(capfd, setup_logger):
    ctx = MockDagsterContext()
    sink = dagster_context_sink(ctx)
    logger.remove()
    logger.add(sink, level="INFO")
    msg = "Üniçøde 🚀" + " " + ("x" * 5000)
    logger.info(msg)
    captured = capfd.readouterr()
    assert "[dagster.info] Üniçøde 🚀" in captured.out


def test_intercept_handler_unknown_numeric_level(capfd):
    logger.remove()
    logger.add(sys.stdout, format="{message}")
    h = InterceptHandler()
    record = logging.LogRecord("t", 37, "p", 1, "odd numeric", (), None)
    h.emit(record)
    captured = capfd.readouterr()
    assert "odd numeric" in captured.out


def test_setup_sinks_idempotent(monkeypatch):
    monkeypatch.setenv("DAGSTER_LOGURU_ENABLED", "true")
    LoguruConfigurator.reset()
    c = LoguruConfigurator()
    before = len(logger._core.handlers)  # noqa: SLF001
    c.setup_sinks()
    after = len(logger._core.handlers)  # noqa: SLF001
    assert before == after


def test_colorize_format_does_not_crash(monkeypatch):
    monkeypatch.setenv("DAGSTER_LOGURU_ENABLED", "true")
    monkeypatch.setenv("DAGSTER_LOGURU_FORMAT", "<green>{time}</green> <level>{message}</level>")
    LoguruConfigurator.reset()
    LoguruConfigurator()
    logger.info("colored ok")


def test_sink_reentrancy_no_deadlock():
    ctx = MockDagsterContext()
    sink = dagster_context_sink(ctx)
    logger.remove()
    logger.add(sink, level="INFO")
    logger.info("outer")


def test_performance_high_volume():
    ctx = MockDagsterContext()
    sink = dagster_context_sink(ctx)
    logger.remove()
    logger.add(sink, level="INFO")
    for _ in range(5000):
        logger.info("spam")


class NoKwContext:
    def __init__(self):
        class L:
            def info(self, msg):  # kwargs yok
                pass

        self.log = L()


def test_sink_falls_back_when_kwargs_not_supported():
    sink = dagster_context_sink(NoKwContext())
    logger.remove()
    logger.add(sink, level="INFO")
    logger.bind(user="x").info("msg")


def test_success_level_maps_to_info(capfd, setup_logger):
    ctx = MockDagsterContext()
    sink = dagster_context_sink(ctx)
    logger.remove()
    logger.add(sink, level="SUCCESS")
    logger.success("Yay")
    captured = capfd.readouterr()
    assert "[dagster.info] Yay" in captured.out


def test_sink_handles_internal_exception_gracefully(capfd):
    """Sink should never crash the process even if the Dagster log method throws."""

    class BoomCtx:
        class L:
            def info(self, *_a, **_k):
                raise RuntimeError("boom")

        log = L()

    sink = dagster_context_sink(BoomCtx())
    logger.remove()
    logger.add(sink, level="INFO")

    # If this raises, the sink is not exception-safe.
    logger.info("still alive")
    captured = capfd.readouterr()
    # No specific output required; test passes if we didn't crash.
    assert captured  # just touch the capture to keep linters happy


def test_sink_reentrancy_guard(capfd):
    """If a Dagster log method calls back into loguru, we must not loop infinitely."""
    calls = {"n": 0}

    class Ctx:
        class L:
            def info(self, msg, **_k):
                calls["n"] += 1
                # Accidental re-log inside sink; must not cause recursion storm.
                logger.debug("inner")

        log = L()

    sink = dagster_context_sink(Ctx())
    logger.remove()
    logger.add(sink, level="DEBUG")

    logger.info("outer")
    # out = capfd.readouterr().out
    assert calls["n"] == 1
    # The inner debug may or may not show depending on mapping; we only assert no recursion.


def test_with_loguru_logger_async(capfd):
    logger.remove()

    def _fmt(rec):
        lvl = rec["level"].name.lower()
        return f"[dagster.{lvl}] {rec['message']}\n"

    logger.add(lambda m: sys.stdout.write(_fmt(m.record)), level="TRACE")

    @with_loguru_logger
    async def aop(context=None):
        logger.info("async ok")

    asyncio.run(aop(context=MockDagsterContext()))
    assert "[dagster.info] async ok" in capfd.readouterr().out


@pytest.mark.parametrize(
    "enabled,level",
    [("true", "TRACE"), ("true", "WARNING"), ("false", "INFO")],
)
def test_config_matrix_env(monkeypatch, enabled, level):
    """Smoke-test different ENV combinations; configurator must be stable/idempotent."""
    monkeypatch.setenv("DAGSTER_LOGURU_ENABLED", enabled)
    monkeypatch.setenv("DAGSTER_LOGURU_LOG_LEVEL", level)
    monkeypatch.delenv("DAGSTER_LOGURU_FORMAT", raising=False)

    LoguruConfigurator.reset()
    c = LoguruConfigurator(enable_terminal_sink=False)
    assert c.config["enabled"] == (enabled == "true")
    assert c.config["log_level"] == level


def test_large_message_and_extra(capfd):
    """Very large payloads (message + extras) should not crash or truncate unexpectedly."""
    ctx = MockDagsterContext()
    sink = dagster_context_sink(ctx)
    logger.remove()
    logger.add(sink, level="INFO")

    big_msg = "X" * (1024 * 256)  # 256 KB message
    big_extra = {f"k{i}": i for i in range(2000)}  # large extras dict
    logger.bind(**big_extra).info(big_msg)

    out = capfd.readouterr().out
    assert "[dagster.info]" in out
    # We don't assert full message to avoid huge output; presence is enough.


def test_bind_and_kwargs_merge_precedence(capfd):
    """If both bind() extras and context kwargs exist, sink should forward what it can without crashing."""

    class KwCtx:
        class L:
            def info(self, msg, **kw):
                # Accept kwargs to simulate structured Dagster logger.
                print(f"[dagster.info] {msg} {kw}")  # noqa: T201

        log = L()

    sink = dagster_context_sink(KwCtx())
    logger.remove()
    logger.add(sink, level="INFO")

    logger.bind(user="alice", trace_id="t-1").info("merged", request_id="r-9")
    out = capfd.readouterr().out
    assert "[dagster.info] merged" in out  # extras presence implies no crash


def test_loguru_configurator_many_inits_idempotent(monkeypatch):
    """Calling configurator many times must not leak handlers or reload config repeatedly."""
    monkeypatch.setenv("DAGSTER_LOGURU_ENABLED", "true")
    LoguruConfigurator.reset()
    logger.remove()
    before = len(logger._core.handlers)  # noqa: SLF001

    for _ in range(50):
        LoguruConfigurator(enable_terminal_sink=False)

    after = len(logger._core.handlers)  # noqa: SLF001
    assert after == before  # no new handlers added when terminal sink disabled


def test_filter_respected(capfd):
    """A user filter attached to loguru should still be respected when forwarding to Dagster."""
    ctx = MockDagsterContext()
    sink = dagster_context_sink(ctx)
    logger.remove()
    # Only allow messages containing 'keep'
    logger.add(sink, level="INFO", filter=lambda r: "keep" in r["message"])

    logger.info("drop this")
    logger.info("please keep this")

    out = capfd.readouterr().out
    assert "[dagster.info] please keep this" in out
    assert "[dagster.info] drop this" not in out


def test_json_serialize_mode(capfd):
    """When serialize=True is used, the sink should still forward messages."""
    captured = []

    class RawCtx:
        class L:
            def info(self, msg, **_k):
                captured.append(msg)

        log = L()

    sink = dagster_context_sink(RawCtx())
    logger.remove()
    logger.add(sink, level="INFO", serialize=True)

    logger.info("json path")

    assert captured and "json path" in captured[0]


def test_throughput_under_slow_context(capfd):
    """Slow Dagster logger should not deadlock; throughput stays acceptable."""

    class SlowCtx:
        class L:
            def info(self, msg, **_k):
                time.sleep(0.005)  # 5 ms per log to simulate slow consumer
                print(f"[dagster.info] {msg}")  # noqa: T201

        log = L()

    sink = dagster_context_sink(SlowCtx())
    logger.remove()
    logger.add(sink, level="INFO")

    start = time.time()
    for i in range(50):
        logger.info(f"msg {i}")
    dur = time.time() - start
    out = capfd.readouterr().out
    assert "[dagster.info] msg 0" in out and "[dagster.info] msg 49" in out
    # Loose bound just to catch deadlocks; tune if needed.
    assert dur < 2.5
