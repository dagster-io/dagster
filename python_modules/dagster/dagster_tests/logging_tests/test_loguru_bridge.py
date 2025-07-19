import os
import sys
import pytest
import logging
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._utils.test import create_test_pipeline_execution_context
from contextlib import contextmanager
from typing import Generator

# Add the repository root to Python path to find loguru_bridge
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from loguru import logger
from loguru_bridge import dagster_context_sink, with_loguru_logger, loguru_enabled

@contextmanager
def capture_loguru_output() -> Generator[list, None, None]:
    """Capture loguru output in a list."""
    output = []
    
    def sink(message):
        # Strip newlines from the message to make assertions easier
        output.append(message.rstrip('\n'))
    
    handler_id = logger.add(sink, format="{message}")
    try:
        yield output
    finally:
        logger.remove(handler_id)

def test_dagster_context_sink():
    """Test that loguru messages are properly forwarded to dagster context."""
    context = create_test_pipeline_execution_context()
    
    with capture_loguru_output() as output:
        logger.add(dagster_context_sink(context), format="{message}")
        
        # Test different log levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.success("Success message")
        
        # Verify messages were captured
        assert "Debug message" in output
        assert "Info message" in output
        assert "Warning message" in output
        assert "Error message" in output
        assert "Success message" in output

def test_with_loguru_logger_decorator():
    """Test the with_loguru_logger decorator."""
    
    @with_loguru_logger
    def sample_function(context: AssetExecutionContext):
        logger.info("Test message from decorated function")
        return "success"
    
    context = create_test_pipeline_execution_context()
    
    with capture_loguru_output() as output:
        result = sample_function(context)
        
        assert result == "success"
        assert "Test message from decorated function" in output

def test_loguru_enabled():
    """Test the loguru_enabled function."""
    # Test with environment variable set to true
    os.environ["DAGSTER_LOGURU_ENABLED"] = "true"
    assert loguru_enabled() is True
    
    # Test with environment variable set to false
    os.environ["DAGSTER_LOGURU_ENABLED"] = "false"
    assert loguru_enabled() is False
    
    # Test with invalid value
    os.environ["DAGSTER_LOGURU_ENABLED"] = "invalid"
    assert loguru_enabled() is True  # Default to True for invalid values
    
    # Clean up
    os.environ.pop("DAGSTER_LOGURU_ENABLED", None)

def test_log_level_propagation():
    """Test that log levels are properly propagated."""
    context = create_test_pipeline_execution_context()
    
    # This test needs special handling as the sink will receive all messages
    # but the context will filter based on level
    
    # Reset outputs before test
    debug_seen = False
    info_seen = False
    
    # Create a custom sink to track what was actually logged at the Dagster level
    original_debug = context.log.debug
    original_info = context.log.info
    
    def mock_debug(msg, **kwargs):
        nonlocal debug_seen
        debug_seen = True
        original_debug(msg, **kwargs)
        
    def mock_info(msg, **kwargs):
        nonlocal info_seen
        info_seen = True
        original_info(msg, **kwargs)
    
    # Replace the log methods with our tracking versions
    context.log.debug = mock_debug
    context.log.info = mock_info
    
    try:
        # Add sink with INFO level - should not forward DEBUG messages to context
        logger.add(dagster_context_sink(context), level="INFO", format="{message}")
        
        # Send messages
        logger.debug("Debug message")
        logger.info("Info message")
        
        # Verify that debug message wasn't sent to the context but info was
        assert not debug_seen, "DEBUG message should not have been forwarded to context"
        assert info_seen, "INFO message should have been forwarded to context"
    finally:
        # Restore original methods
        context.log.debug = original_debug
        context.log.info = original_info

def test_context_integration():
    """Test integration with dagster context."""
    context = create_test_pipeline_execution_context()
    
    with capture_loguru_output() as output:
        logger.add(dagster_context_sink(context), format="{message}")
        
        # Test context integration
        logger.info("Message with context")
        
        assert "Message with context" in output
        # You might want to add more specific assertions about how the message
        # appears in the dagster context logs

def test_error_handling():
    """Test error handling in the bridge."""
    context = create_test_pipeline_execution_context()
    
    with capture_loguru_output() as output:
        logger.add(dagster_context_sink(context), format="{message}")
        
        # Test with various potentially problematic inputs
        logger.info("")  # Empty message
        logger.info(None)  # None message
        logger.info({"complex": "object"})  # Complex object
        
        # Verify no exceptions were raised and messages were handled
        assert len(output) == 3

def test_structured_logging():
    """Test structured logging with metadata."""
    context = create_test_pipeline_execution_context()
    
    with capture_loguru_output() as output:
        logger.add(dagster_context_sink(context), format="{message}")
        
        # Test with extra fields
        logger.bind(user_id="123", action="test").info("Structured log message")
        logger.bind(correlation_id="abc").bind(request_id="xyz").info("Chained binding")
        
        assert "Structured log message" in output
        assert "Chained binding" in output

def test_nested_decorator_calls():
    """Test nested function calls with @with_loguru_logger decorator."""
    @with_loguru_logger
    def outer_function(context):
        logger.info("Outer function start")
        result = inner_function(context)
        logger.info("Outer function end")
        return result

    @with_loguru_logger
    def inner_function(context):
        logger.info("Inner function executing")
        return "inner success"

    context = create_test_pipeline_execution_context()
    
    with capture_loguru_output() as output:
        result = outer_function(context)
        
        assert result == "inner success"
        assert "Outer function start" in output
        assert "Inner function executing" in output
        assert "Outer function end" in output

def test_decorator_error_propagation():
    """Test error propagation in decorated functions."""
    @with_loguru_logger
    def error_function(context):
        logger.info("Before error")
        raise ValueError("Test error")
        logger.info("After error")  # Should not be logged

    context = create_test_pipeline_execution_context()
    
    with capture_loguru_output() as output:
        with pytest.raises(ValueError, match="Test error"):
            error_function(context)
        
        assert "Before error" in output
        assert "After error" not in output

def test_concurrent_logging():
    """Test concurrent logging operations."""
    import threading
    import time

    @with_loguru_logger
    def thread_function(context, thread_id):
        logger.info(f"Thread {thread_id} start")
        time.sleep(0.1)  # Simulate work
        logger.info(f"Thread {thread_id} end")

    context = create_test_pipeline_execution_context()
    
    with capture_loguru_output() as output:
        threads = []
        for i in range(3):
            thread = threading.Thread(
                target=thread_function,
                args=(context, i)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify all thread messages were captured
        for i in range(3):
            assert f"Thread {i} start" in "".join(output)
            assert f"Thread {i} end" in "".join(output)

if __name__ == "__main__":
    pytest.main([__file__])
