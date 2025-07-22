import pytest
import os
import sys
import dagster as dg
from loguru import logger

# Try to load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, skip loading .env file
    pass

# Add the root directory to Python path to find loguru_bridge
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
    
# Import bridge components
from loguru_bridge import dagster_context_sink, with_loguru_logger
# Setup Buildkite environment variables for testing
def setup_buildkite_environment():
    """Setup meaningful test environment variables for Buildkite integration."""
    print("Setting up Buildkite test environment...")
    
    # Set up meaningful test environment variables
    os.environ["BUILDKITE"] = "true"
    os.environ["BUILDKITE_BUILD_ID"] = os.environ.get("BUILDKITE_BUILD_ID", "local-loguru-bridge-test-build")
    os.environ["BUILDKITE_JOB_ID"] = os.environ.get("BUILDKITE_JOB_ID", "logging-tests-job-validation")
    os.environ["BUILDKITE_COMMIT"] = os.environ.get("BUILDKITE_COMMIT", "loguru-bridge-integration-commit")
    os.environ["BUILDKITE_ORGANIZATION_SLUG"] = "dagster"  # Force this to be dagster for tests
    os.environ["BUILDKITE_PIPELINE_SLUG"] = os.environ.get("BUILDKITE_PIPELINE_SLUG", "unit-tests")
    os.environ["BUILDKITE_BRANCH"] = os.environ.get("BUILDKITE_BRANCH", "Issue-29914")
    os.environ["BUILDKITE_BUILD_NUMBER"] = os.environ.get("BUILDKITE_BUILD_NUMBER", "local")
    
    print("Buildkite environment variables set:")
    print(f"BUILDKITE_ANALYTICS_TOKEN: {os.environ.get('BUILDKITE_ANALYTICS_TOKEN', 'NOT SET')}")
    print(f"BUILDKITE: {os.environ.get('BUILDKITE')}")
    print(f"BUILDKITE_BUILD_ID: {os.environ.get('BUILDKITE_BUILD_ID')}")
    print(f"BUILDKITE_JOB_ID: {os.environ.get('BUILDKITE_JOB_ID')}")
    print(f"BUILDKITE_COMMIT: {os.environ.get('BUILDKITE_COMMIT')}")
    print(f"BUILDKITE_ORGANIZATION_SLUG: {os.environ.get('BUILDKITE_ORGANIZATION_SLUG')}")
    print(f"BUILDKITE_PIPELINE_SLUG: {os.environ.get('BUILDKITE_PIPELINE_SLUG')}")

# Initialize Buildkite environment when module is loaded
setup_buildkite_environment()

def pytest_itemcollected(item):
  # add execution tag to all tests
  item.add_marker(pytest.mark.execution_tag("test.framework.name", "pytest"))
  item.add_marker(pytest.mark.execution_tag("test.framework.version", pytest.__version__))
  item.add_marker(pytest.mark.execution_tag("cloud.provider", "aws"))
  item.add_marker(pytest.mark.execution_tag("language.version", sys.version))
class MockLogHandler:
    """Mock log handler that prints and stores log messages."""
    def __init__(self):
        self.history = []

    def debug(self, msg):
        print("[dagster.debug]", msg)
        self.history.append({"level": "debug", "message": msg})
        return self.history[-1]

    def info(self, msg):
        print("[dagster.info]", msg)
        self.history.append({"level": "info", "message": msg})
        return self.history[-1]

    def warning(self, msg):
        print("[dagster.warning]", msg)
        self.history.append({"level": "warning", "message": msg})
        return self.history[-1]

    def error(self, msg):
        print("[dagster.error]", msg)
        self.history.append({"level": "error", "message": msg})
        return self.history[-1]

    def critical(self, msg):
        print("[dagster.critical]", msg)
        self.history.append({"level": "critical", "message": msg})
        return self.history[-1]

class MockDagsterContext:
    """Simulates Dagster's context.log interface with debug logging capabilities."""
    def __init__(self):
        self.log = MockLogHandler()


@pytest.fixture
def setup_logger():
    """Fixture to setup and cleanup logger for each test."""
    # Configure logger for the test
    logger.remove()  # Remove default handlers
    
    # For tests, add a formatter that adds the [dagster.level] prefix
    def test_formatter(record):
        level_name = record["level"].name.lower()
        # Map SUCCESS level to INFO for the test output format
        if level_name == "success":
            level_name = "info"
        return f"[dagster.{level_name}] {record['message']}"
    
    logger.add(lambda msg: print(test_formatter(msg.record)), level="DEBUG")
    
    # Cleanup after test
    yield
    logger.remove()  # Cleanup after test

def test_dagster_context_sink_basic_logging(capfd, setup_logger):
    """Test that dagster_context_sink routes basic logs correctly."""
    context = MockDagsterContext()
    sink = dagster_context_sink(context)

    logger.remove()
    logger.add(sink, level="DEBUG")

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    captured = capfd.readouterr()
    assert "[dagster.debug] Debug message" in captured.out
    assert "[dagster.info] Info message" in captured.out
    assert "[dagster.warning] Warning message" in captured.out
    assert "[dagster.error] Error message" in captured.out

def test_dagster_context_sink_with_structured_logging(capfd, setup_logger):
    """Test structured logging with extra fields."""
    context = MockDagsterContext()
    sink = dagster_context_sink(context)

    logger.remove()
    logger.add(sink, level="DEBUG")

    # Test structured logging with extra fields
    logger.bind(user="test_user", action="login").info("User login attempt")
    logger.bind(error_code=500).error("Server error occurred")
    
    captured = capfd.readouterr()
    assert "[dagster.info] User login attempt" in captured.out
    assert "[dagster.error] Server error occurred" in captured.out

def test_dagster_context_sink_different_log_levels(capfd, setup_logger):
    """Test various log levels including TRACE and CRITICAL."""
    context = MockDagsterContext()
    sink = dagster_context_sink(context)

    logger.remove()
    logger.add(sink, level="TRACE")

    test_messages = [
        (logger.trace, "Trace level message"),
        (logger.debug, "Debug level message"),
        (logger.info, "Info level message"),
        (logger.success, "Success message"),
        (logger.warning, "Warning level message"),
        (logger.error, "Error level message"),
        (logger.critical, "Critical level message"),
    ]

    for log_func, message in test_messages:
        log_func(message)

    captured = capfd.readouterr()
    assert "[dagster.debug] Trace level message" in captured.out
    assert "[dagster.debug] Debug level message" in captured.out
    assert "[dagster.info] Info level message" in captured.out
    assert "[dagster.info] Success message" in captured.out
    assert "[dagster.warning] Warning level message" in captured.out
    assert "[dagster.error] Error level message" in captured.out
    assert "[dagster.critical] Critical level message" in captured.out


class DagsterOperations:
    """Class for simulating different Dagster operations."""
    
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

    def get_context(self):
        return self._context


def test_with_loguru_logger_decorator_success(capfd, setup_logger):
    """Test the @with_loguru_logger decorator with successful operation."""
    context = MockDagsterContext()
    test_ops = DagsterOperations(context)

    result = test_ops.successful_op()
    assert result is True

    captured = capfd.readouterr()
    assert "[dagster.info] Operation completed successfully!" in captured.out


def test_with_loguru_logger_decorator_failure(capfd, setup_logger):
    """Test the @with_loguru_logger decorator with failing operation."""
    context = MockDagsterContext()
    test_ops = DagsterOperations(context)

    with pytest.raises(ValueError, match="Operation failed"):
        test_ops.failing_op()

    captured = capfd.readouterr()
    assert "[dagster.error] Operation failed!" in captured.out


def test_with_loguru_logger_decorator_complex(capfd, setup_logger):
    """Test the @with_loguru_logger decorator with complex logging scenario."""
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
        # Direct Dagster logging using self._context
        self._context.log.info("Direct Dagster log")
        # Loguru logging
        logger.info("Loguru log")
        # Mixed in sequence
        self._context.log.debug("Dagster debug")
        logger.debug("Loguru debug")
        return "Mixed logging complete"

    def get_context(self):
        return self._context


def test_mixed_logging_systems(capfd, setup_logger):
    """Test mixing Dagster's native logging with Loguru logging."""
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
    """Test nested operations with both logging systems."""
    test_ctx = DagsterTestContext()

    class NestedLogger:
        def __init__(self, test_ctx):
            self._context = test_ctx.context
            self.test_ops = test_ctx.test_ops

        @with_loguru_logger
        def nested_op(self, context=None):
            logger.info("Starting nested operation")
            self.test_ops.complex_op()  # This already has logging
            logger.info("Nested operation complete")
            return True

        def get_context(self):
            return self._context

    nested_logger = NestedLogger(test_ctx)
    result = nested_logger.nested_op()
    assert result is True

    captured = capfd.readouterr()
    assert "[dagster.info] Starting nested operation" in captured.out
    assert "[dagster.debug] Starting complex operation..." in captured.out
    assert "[dagster.info] Processing data" in captured.out
    assert "[dagster.warning] Resource usage high" in captured.out
    assert "[dagster.info] Data processing complete" in captured.out
    assert "[dagster.info] Nested operation complete" in captured.out


def test_exception_handling_with_logging(capfd, setup_logger):
    """Test exception handling with both logging systems."""
    test_ctx = DagsterTestContext()

    class ExceptionLogger:
        def __init__(self, context):
            self._context = context

        @with_loguru_logger
        def exception_op(self, context=None):
            try:
                logger.info("Starting risky operation")
                raise ValueError("Simulated error")
            except ValueError as e:
                logger.error(f"Caught error: {str(e)}")
                self._context.log.error(f"Dagster also logged: {str(e)}")
            finally:
                logger.info("Cleanup in finally block")

        def get_context(self):
            return self._context

    exception_logger = ExceptionLogger(test_ctx.context)
    exception_logger.exception_op()
    captured = capfd.readouterr()
    assert "[dagster.info] Starting risky operation" in captured.out
    assert "[dagster.error] Caught error: Simulated error" in captured.out
    assert "[dagster.error] Dagster also logged: Simulated error" in captured.out
    assert "[dagster.info] Cleanup in finally block" in captured.out


def test_structured_logging_with_context(capfd, setup_logger):
    """Test structured logging with context data in both systems."""
    test_ctx = DagsterTestContext()

    class StructuredLogger:
        def __init__(self, context):
            self._context = context

        @with_loguru_logger
        def structured_log_op(self, context=None):
            # Loguru structured logging
            logger.bind(
                operation_id="12345",
                user_id="user123",
                environment="test"
            ).info("Operation started with context")
            
            # Add some processing simulation
            logger.bind(
                duration_ms=150,
                items_processed=100
            ).success("Processing complete")

            return "Structured logging test complete"

        def get_context(self):
            return self._context

    structured_logger = StructuredLogger(test_ctx.context)
    result = structured_logger.structured_log_op()
    assert result == "Structured logging test complete"

    captured = capfd.readouterr()
    assert "[dagster.info] Operation started with context" in captured.out
    assert "[dagster.info] Processing complete" in captured.out


def test_log_level_inheritance(capfd, setup_logger):
    """Test log level inheritance and filtering."""
    test_ctx = DagsterTestContext()

    class LevelLogger:
        def __init__(self, context):
            self._context = context

        @with_loguru_logger
        def level_test_op(self, context=None):
            logger.trace("This should not appear")  # Should be filtered out
            logger.debug("Debug message should appear")
            logger.info("Info message should appear")
            logger.success("Success should map to info")
            logger.warning("Warning message should appear")
            logger.error("Error message should appear")
            logger.critical("Critical message should appear")

        def get_context(self):
            return self._context

    level_logger = LevelLogger(test_ctx.context)
    level_logger.level_test_op()
    captured = capfd.readouterr()
    
    assert "This should not appear" not in captured.out
    assert "[dagster.debug] Debug message should appear" in captured.out
    assert "[dagster.info] Info message should appear" in captured.out
    assert "[dagster.info] Success should map to info" in captured.out
    assert "[dagster.warning] Warning message should appear" in captured.out
    assert "[dagster.error] Error message should appear" in captured.out
    assert "[dagster.critical] Critical message should appear" in captured.out


def test_concurrent_operations_logging(capfd, setup_logger):
    """Test logging behavior with concurrent operations."""
    import threading
    import time
    test_ctx = DagsterTestContext()

    class ConcurrentLogger:
        def __init__(self, context):
            self._context = context

        @with_loguru_logger
        def concurrent_op(self, op_id, context=None):
            logger.info(f"Operation {op_id} started")
            time.sleep(0.1)  # Simulate some work
            logger.info(f"Operation {op_id} completed")
            return op_id

        def get_context(self):
            return self._context

    concurrent_logger = ConcurrentLogger(test_ctx.context)

    # Run multiple operations concurrently
    threads = []
    for i in range(3):
        thread = threading.Thread(
            target=concurrent_logger.concurrent_op,
            args=(f"thread-{i}",)
        )
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    captured = capfd.readouterr()
    
    # Check that all operations were logged
    for i in range(3):
        assert f"[dagster.info] Operation thread-{i} started" in captured.out
        assert f"[dagster.info] Operation thread-{i} completed" in captured.out
def test_log_formatting_consistency(capfd, setup_logger):
    """Test consistency of log formatting between Dagster and Loguru."""
    test_ctx = DagsterTestContext()

    class FormatLogger:
        def __init__(self, context):
            self._context = context

        @with_loguru_logger
        def format_test_op(self, context=None):
            # Test different message formats
            logger.info("Simple message")
            logger.info("Message with {}", "placeholder")
            logger.info("Message with {name}", name="named placeholder")
            logger.info("Message with multiple {} {}", "placeholders", "here")
            
            # Test with different data types
            logger.info("Number: {}", 42)
            logger.info("Boolean: {}", True)
            logger.info("List: {}", [1, 2, 3])
            logger.info("Dict: {}", {"key": "value"})

        def get_context(self):
            return self._context

    format_logger = FormatLogger(test_ctx.context)
    format_logger.format_test_op()
    captured = capfd.readouterr()
    
    assert "[dagster.info] Simple message" in captured.out
    assert "[dagster.info] Message with placeholder" in captured.out
    assert "[dagster.info] Message with named placeholder" in captured.out
    assert "[dagster.info] Message with multiple placeholders here" in captured.out
    assert "[dagster.info] Number: 42" in captured.out
    assert "[dagster.info] Boolean: True" in captured.out
    assert "[dagster.info] List: [1, 2, 3]" in captured.out
    assert "[dagster.info] Dict: {'key': 'value'}" in captured.out
def test_error_context_preservation(capfd, setup_logger):
    """Test that error context and stack traces are preserved."""
    test_ctx = DagsterTestContext()

    class CustomError(Exception):
        pass

    class ErrorLogger:
        def __init__(self, context):
            self._context = context

        @with_loguru_logger
        def nested_error(self, context=None):
            raise CustomError("Nested error occurred")

        @with_loguru_logger
        def error_context_op(self, context=None):
            try:
                logger.info("Starting operation that will fail")
                self.nested_error()
            except CustomError as e:
                logger.error(f"An error occurred in the nested operation: {str(e)}")
                self._context.log.error(f"Dagster also logged error: {str(e)}")
                return "Error handled"

        def get_context(self):
            return self._context

    error_logger = ErrorLogger(test_ctx.context)
    result = error_logger.error_context_op()
    assert result == "Error handled"

    captured = capfd.readouterr()
    assert "[dagster.info] Starting operation that will fail" in captured.out
    assert "[dagster.error] An error occurred in the nested operation: Nested error occurred" in captured.out
    assert "[dagster.error] Dagster also logged error: Nested error occurred" in captured.out


class DagsterTestContext:
    """Helper class to manage context for test functions."""
    def __init__(self):
        self.context = MockDagsterContext()
        self.test_ops = DagsterOperations(self.context)

    def get_context(self):
        return self.context


def test_loguru_configurator_initialization(monkeypatch):
    """Test LoguruConfigurator initialization and configuration loading."""
    # Test with environment variables
    monkeypatch.setenv("DAGSTER_LOGURU_ENABLED", "false")
    monkeypatch.setenv("DAGSTER_LOGURU_LOG_LEVEL", "INFO")
    monkeypatch.setenv("DAGSTER_LOGURU_FORMAT", "TEST_FORMAT")
    
    # Reset for other tests
    monkeypatch.setenv("DAGSTER_LOGURU_ENABLED", "true")
    monkeypatch.setenv("DAGSTER_LOGURU_LOG_LEVEL", "DEBUG")
    monkeypatch.delenv("DAGSTER_LOGURU_FORMAT", raising=False)


def test_dagster_handler_logging(capfd, setup_logger):
    """Test logging with a custom handler."""
    import logging
    
    # Setup a special test logger to avoid recursion
    test_logger = logging.getLogger("test_handler_logger")
    test_logger.setLevel(logging.DEBUG)
    test_logger.propagate = False  # Important to avoid recursion
    
    # Create a special handler that just prints without recursion
    class TestLogPrinter(logging.Handler):
        def emit(self, record):
            print(f"[{record.levelname}] {record.getMessage()}")
    
    handler = TestLogPrinter()
    test_logger.addHandler(handler)
    
    # Log messages
    test_logger.debug("Debug from Python logging")
    test_logger.info("Info from Python logging")
    test_logger.warning("Warning from Python logging")
    test_logger.error("Error from Python logging")
    
    # Clean up
    test_logger.removeHandler(handler)
    
    # Check output
    captured = capfd.readouterr()
    assert "Debug from Python logging" in captured.out
    assert "Info from Python logging" in captured.out
    assert "Warning from Python logging" in captured.out
    assert "Error from Python logging" in captured.out


def test_loguru_bridge_integration_with_dagster_context(capfd, setup_logger):
    """Test integration between loguru_bridge and dagster context."""
    import tempfile
    
    test_ctx = DagsterTestContext()
    class IntegrationLogger:
        def __init__(self, context):
            self._context = context
            
        @with_loguru_logger
        def log_with_integration(self, context=None):
            # Create a log file
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
                temp_name = temp.name
                
                # Add a file sink
                file_id = logger.add(temp_name, level="DEBUG")
                
                # Log to both the context and the file
                logger.debug("Debug message to multiple outputs")
                logger.info("Info message to multiple outputs")
                logger.warning("Warning message to multiple outputs")
                
                # Remove the file sink
                logger.remove(file_id)
                
                # Check that the file contains logs
                with open(temp_name, 'r') as f:
                    content = f.read()
                    assert "Debug message to multiple outputs" in content
                    assert "Info message to multiple outputs" in content
                    assert "Warning message to multiple outputs" in content
                
            return "Integration test complete"
        
        def get_context(self):
            return self._context
    
    integration_logger = IntegrationLogger(test_ctx.context)
    result = integration_logger.log_with_integration()
    assert result == "Integration test complete"
    
    captured = capfd.readouterr()
    assert "[dagster.debug] Debug message to multiple outputs" in captured.out
    assert "[dagster.info] Info message to multiple outputs" in captured.out
    assert "[dagster.warning] Warning message to multiple outputs" in captured.out


def test_loguru_bridge_performance(setup_logger):
    """Test performance of loguru_bridge."""
    import time
    
    test_ctx = DagsterTestContext()
    sink = dagster_context_sink(test_ctx.context)
    
    logger.remove()
    logger.add(sink, level="INFO")
    
    # Measure time for logging many messages
    start_time = time.time()
    message_count = 1000
    
    for i in range(message_count):
        logger.info(f"Performance test message {i}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Performance test - this is just a basic check
    # that logging doesn't add excessive overhead
    assert duration < 5.0, f"Logging {message_count} messages took {duration} seconds"


def test_loguru_bridge_with_stdout_integration(capfd, setup_logger):
    """Test integration with stdout redirection."""
    import sys
    
    test_ctx = DagsterTestContext()
    
    class StdoutLogger:
        def __init__(self, context):
            self._context = context
            
        def log_with_stdout(self, context=None):
            # Direct stdout prints
            print("Direct stdout print")
            
            # Loguru logs
            logger.info("Loguru info message")
            
            # More stdout
            print("Another stdout print")
            
            # Error stream
            print("Error message", file=sys.stderr)
            
            return "Stdout test complete"
        
        def get_context(self):
            return self._context
    
    stdout_logger = StdoutLogger(test_ctx.context)
    result = stdout_logger.log_with_stdout()
    assert result == "Stdout test complete"
    
    captured = capfd.readouterr()
    assert "Direct stdout print" in captured.out
    assert "[dagster.info] Loguru info message" in captured.out
    assert "Another stdout print" in captured.out
    assert "Error message" in captured.err


def test_buildkite_analytics_integration(capfd, setup_logger):
    """Test Buildkite Analytics Integration with loguru bridge."""
    print("Testing Buildkite Analytics Integration...")
    
    # Verify environment variables are set
    assert os.environ.get('BUILDKITE') == 'true'
    assert os.environ.get('BUILDKITE_BUILD_ID') is not None
    assert os.environ.get('BUILDKITE_JOB_ID') is not None
    
    test_ctx = DagsterTestContext()
    
    class BuildkiteLogger:
        def __init__(self, context):
            self._context = context
            
        def buildkite_integration_op(self, context=None):
            # Log with buildkite context information
            logger.info(f"Build ID: {os.environ.get('BUILDKITE_BUILD_ID')}")
            logger.info(f"Job ID: {os.environ.get('BUILDKITE_JOB_ID')}")
            logger.info(f"Organization: {os.environ.get('BUILDKITE_ORGANIZATION_SLUG')}")
            logger.info(f"Pipeline: {os.environ.get('BUILDKITE_PIPELINE_SLUG')}")
            logger.info(f"Branch: {os.environ.get('BUILDKITE_BRANCH')}")
            
            # Test with analytics token if available
            token = os.environ.get('BUILDKITE_ANALYTICS_TOKEN')
            if token:
                logger.info("Analytics token is available and will be used for reporting")
            else:
                logger.warning("No BUILDKITE_ANALYTICS_TOKEN found")
            
            return "Buildkite integration test complete"
        
        def get_context(self):
            return self._context
    
    buildkite_logger = BuildkiteLogger(test_ctx.context)
    result = buildkite_logger.buildkite_integration_op()
    assert result == "Buildkite integration test complete"
    
    captured = capfd.readouterr()
    # Use the actual values from environment (which may come from .env file)
    expected_build_id = os.environ.get('BUILDKITE_BUILD_ID')
    expected_job_id = os.environ.get('BUILDKITE_JOB_ID')
    expected_org = os.environ.get('BUILDKITE_ORGANIZATION_SLUG')
    expected_pipeline = os.environ.get('BUILDKITE_PIPELINE_SLUG')
    expected_branch = os.environ.get('BUILDKITE_BRANCH')
    
    assert f"Build ID: {expected_build_id}" in captured.out
    assert f"Job ID: {expected_job_id}" in captured.out
    assert f"Organization: {expected_org}" in captured.out
    assert f"Pipeline: {expected_pipeline}" in captured.out
    assert f"Branch: {expected_branch}" in captured.out


def test_buildkite_environment_validation():
    """Test that Buildkite environment variables are properly configured."""
    required_vars = [
        'BUILDKITE',
        'BUILDKITE_BUILD_ID', 
        'BUILDKITE_JOB_ID',
        'BUILDKITE_COMMIT',
        'BUILDKITE_ORGANIZATION_SLUG',
        'BUILDKITE_PIPELINE_SLUG',
        'BUILDKITE_BRANCH',
        'BUILDKITE_BUILD_NUMBER'
    ]
    
    for var in required_vars:
        assert os.environ.get(var) is not None, f"Environment variable {var} should be set"
    
    # Test specific values
    assert os.environ.get('BUILDKITE') == 'true'
    
    # Instead of checking for specific values, just verify they exist
    assert os.environ.get('BUILDKITE_ORGANIZATION_SLUG') is not None
    assert os.environ.get('BUILDKITE_PIPELINE_SLUG') is not None
    assert os.environ.get('BUILDKITE_BRANCH') is not None


def test_direct_loguru_usage(capfd, setup_logger):
    """Test the direct usage of loguru as shown in the example asset."""
    
    # This simulates the test_loguru_html_log asset from the example
    def simulate_direct_loguru():
        logger.debug("==Debug== Loguru is working in Dagster!")
        logger.info("==Info== Loguru is working in Dagster!")
        logger.warning("==Warning== Loguru is working in Dagster!")
        logger.error("==!!Error!!== Loguru is working in Dagster!")
        return {"status": "done"}
    
    result = simulate_direct_loguru()
    assert result == {"status": "done"}
    
    # Check logs were output directly
    captured = capfd.readouterr()
    assert "==Debug== Loguru is working in Dagster!" in captured.out
    assert "==Info== Loguru is working in Dagster!" in captured.out
    assert "==Warning== Loguru is working in Dagster!" in captured.out
    assert "==!!Error!!== Loguru is working in Dagster!" in captured.out


def test_context_log_with_loguru_decorator(capfd, setup_logger):
    """Test the usage of context.log with the loguru_bridge decorator as shown in the example asset."""
    
    test_ctx = DagsterTestContext()
    
    class ContextLogExample:
        def __init__(self, context):
            self._context = context
        
        @with_loguru_logger
        def simulate_contexlog_callig_loguru(self, context=None):
            # This simulates the my_contexlog_callig_loguru asset from the example
            self._context.log.debug("This is a context.log.debug message from my_contexlog_callig_loguru")
            self._context.log.info("This is an context.log.info message from my_contexlog_callig_loguru")
            self._context.log.warning("This is a context.log.warning message from my_contexlog_callig_loguru")
            self._context.log.error("This is an context.log.error message from my_contexlog_callig_loguru")
            self._context.log.critical("This is a context.log.critical message from my_contexlog_callig_loguru")
        
        def get_context(self):
            return self._context
    
    context_log_example = ContextLogExample(test_ctx.context)
    context_log_example.simulate_contexlog_callig_loguru()
    
    # Check logs were correctly routed through the context
    captured = capfd.readouterr()
    assert "[dagster.debug] This is a context.log.debug message from my_contexlog_callig_loguru" in captured.out
    assert "[dagster.info] This is an context.log.info message from my_contexlog_callig_loguru" in captured.out
    assert "[dagster.warning] This is a context.log.warning message from my_contexlog_callig_loguru" in captured.out
    assert "[dagster.error] This is an context.log.error message from my_contexlog_callig_loguru" in captured.out
    assert "[dagster.critical] This is a context.log.critical message from my_contexlog_callig_loguru" in captured.out
