"""Tests for the diagnostics module."""

import json
import tempfile
from pathlib import Path

from dagster_dg_cli.cli.scaffold.branch.claude.diagnostics import (
    AIInteraction,
    ClaudeDiagnostics,
    ContextGathering,
    DiagnosticsEntry,
    PerformanceMetrics,
    create_claude_diagnostics_service,
)


class TestClaudeDiagnosticsService:
    def test_initialization_off_by_default(self):
        service = ClaudeDiagnostics()
        assert service.level == "off"
        assert service.correlation_id is not None
        assert service.entries == []

    def test_initialization_with_custom_params(self):
        correlation_id = "test-correlation-id"
        output_dir = Path("/tmp/test")
        service = ClaudeDiagnostics(
            level="debug",
            output_dir=output_dir,
            correlation_id=correlation_id,
        )
        assert service.level == "debug"
        assert service.correlation_id == correlation_id
        assert service.output_dir == output_dir

    def test_should_log_hierarchy(self):
        # Test logging hierarchy: error < info < debug
        service = ClaudeDiagnostics(level="info")

        assert service._should_log("error") is True  # noqa: SLF001
        assert service._should_log("info") is True  # noqa: SLF001
        assert service._should_log("debug") is False  # noqa: SLF001

        service.level = "debug"
        assert service._should_log("error") is True  # noqa: SLF001
        assert service._should_log("info") is True  # noqa: SLF001
        assert service._should_log("debug") is True  # noqa: SLF001

        service.level = "error"
        assert service._should_log("error") is True  # noqa: SLF001
        assert service._should_log("info") is False  # noqa: SLF001
        assert service._should_log("debug") is False  # noqa: SLF001

    def test_should_not_log_when_off(self):
        service = ClaudeDiagnostics(level="off")

        assert service._should_log("error") is False  # noqa: SLF001
        assert service._should_log("info") is False  # noqa: SLF001
        assert service._should_log("debug") is False  # noqa: SLF001

    def test_log_creates_entry(self):
        service = ClaudeDiagnostics(level="info")

        service.log(
            level="info", category="test_category", message="test message", data={"key": "value"}
        )

        assert len(service.entries) == 1
        entry = service.entries[0]
        assert entry.level == "info"
        assert entry.category == "test_category"
        assert entry.message == "test message"
        assert entry.data == {"key": "value"}
        assert entry.correlation_id == service.correlation_id

    def test_log_does_not_create_entry_when_level_too_low(self):
        service = ClaudeDiagnostics(level="error")

        service.log(level="info", category="test_category", message="test message")

        assert len(service.entries) == 0

    def test_data_logging_without_sanitization(self):
        service = ClaudeDiagnostics(level="info")

        test_data = {
            "api_key": "sk-1234567890abcdef",  # This will no longer be redacted
            "secret_token": "secret-value",
            "password": "mypassword",
            "normal_key": "normal_value",
        }

        service.log(level="info", category="test", message="message", data=test_data)

        entry = service.entries[0]
        # Data should be logged as-is without sanitization
        assert entry.data["api_key"] == "sk-1234567890abcdef"
        assert entry.data["secret_token"] == "secret-value"
        assert entry.data["password"] == "mypassword"
        assert entry.data["normal_key"] == "normal_value"

    def test_ai_interaction_logging(self):
        service = ClaudeDiagnostics(level="info")

        interaction = AIInteraction(
            correlation_id="test-id",
            timestamp="2024-01-01T00:00:00",
            prompt="test prompt",
            response="test response",
            token_count=100,
            allowed_tools=["tool1", "tool2"],
            duration_ms=500.0,
        )

        service.log_ai_interaction(interaction)

        assert len(service.entries) == 1
        entry = service.entries[0]
        assert entry.category == "ai_interaction"
        assert entry.data["prompt_length"] == len("test prompt")
        assert entry.data["response_length"] == len("test response")
        assert entry.data["token_count"] == 100
        assert entry.data["allowed_tools"] == ["tool1", "tool2"]
        assert entry.data["duration_ms"] == 500.0

    def test_context_gathering_logging(self):
        service = ClaudeDiagnostics(level="debug")

        context = ContextGathering(
            correlation_id="test-id",
            timestamp="2024-01-01T00:00:00",
            files_analyzed=["file1.py", "file2.py"],
            patterns_detected=["pattern1", "pattern2"],
            decisions_made={"decision1": "value1"},
        )

        service.log_context_gathering(context)

        assert len(service.entries) == 1
        entry = service.entries[0]
        assert entry.category == "context_gathering"
        assert entry.data["files_count"] == 2
        assert entry.data["files_analyzed"] == ["file1.py", "file2.py"]
        assert entry.data["patterns_detected"] == ["pattern1", "pattern2"]

    def test_performance_logging(self):
        service = ClaudeDiagnostics(level="debug")

        metrics = PerformanceMetrics(
            correlation_id="test-id",
            timestamp="2024-01-01T00:00:00",
            operation="test_operation",
            duration_ms=250.0,
            phase="test_phase",
        )

        service.log_performance(metrics)

        assert len(service.entries) == 1
        entry = service.entries[0]
        assert entry.category == "performance"
        assert entry.data["operation"] == "test_operation"
        assert entry.data["phase"] == "test_phase"
        assert entry.data["duration_ms"] == 250.0

    def test_time_operation_context_manager(self):
        service = ClaudeDiagnostics(level="debug")

        with service.time_operation("test_op", "test_phase"):
            # Simulate some work
            pass

        assert len(service.entries) == 1
        entry = service.entries[0]
        assert entry.category == "performance"
        assert entry.data["operation"] == "test_op"
        assert entry.data["phase"] == "test_phase"
        assert entry.data["duration_ms"] >= 0

    def test_convenience_methods(self):
        service = ClaudeDiagnostics(level="debug")

        service.error(category="test_cat", message="error message")
        service.info(category="test_cat", message="info message")
        service.debug(category="test_cat", message="debug message")

        assert len(service.entries) == 3
        assert service.entries[0].level == "error"
        assert service.entries[1].level == "info"
        assert service.entries[2].level == "debug"

    def test_flush_writes_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            service = ClaudeDiagnostics(level="info", output_dir=output_dir)

            service.info(category="test", message="test message", data={"key": "value"})

            output_path = service.flush()

            assert output_path is not None
            assert output_path.exists()

            # Verify file contents - parse JSONL format
            lines = output_path.read_text().strip().split("\n")
            assert len(lines) >= 3  # session_start, entry, session_end

            # Parse each line as JSON
            session_start = json.loads(lines[0])
            entry = json.loads(lines[1])
            session_end = json.loads(lines[2])

            # Verify session_start
            assert session_start["type"] == "session_start"
            assert session_start["correlation_id"] == service.correlation_id
            assert session_start["level"] == "info"

            # Verify entry
            assert entry["type"] == "entry"
            assert entry["correlation_id"] == service.correlation_id
            assert entry["level"] == "info"
            assert entry["category"] == "test"
            assert entry["message"] == "test message"
            assert entry["data"] == {"key": "value"}

            # Verify session_end
            assert session_end["type"] == "session_end"
            assert session_end["correlation_id"] == service.correlation_id

            # Verify entries are cleared after flush
            assert len(service.entries) == 0

    def test_flush_returns_none_when_off(self):
        service = ClaudeDiagnostics(level="off")
        service.entries = []  # Ensure no entries

        output_path = service.flush()

        assert output_path is None

    def test_flush_returns_none_when_no_entries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            service = ClaudeDiagnostics(level="info", output_dir=output_dir)

            output_path = service.flush()

            assert output_path is None


class TestClaudeDiagnosticsServiceCreation:
    def test_create_diagnostics_service_defaults(self):
        service = create_claude_diagnostics_service()

        assert service.level == "off"
        assert service.correlation_id is not None
        assert service.output_dir == Path(tempfile.gettempdir()) / "dg" / "diagnostics"

    def test_create_diagnostics_service_with_params(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            correlation_id = "test-correlation-id"

            service = create_claude_diagnostics_service(
                level="debug",
                output_dir=output_dir,
                correlation_id=correlation_id,
            )

            assert service.level == "debug"
            assert service.correlation_id == correlation_id
            assert service.output_dir == output_dir

    def test_create_diagnostics_service_string_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = create_claude_diagnostics_service(
                level="info",
                output_dir=temp_dir,
            )

            assert service.level == "info"
            assert service.output_dir == Path(temp_dir)


class TestDiagnosticsDataModels:
    def test_diagnostics_entry_creation(self):
        entry = DiagnosticsEntry(
            correlation_id="test-id",
            timestamp="2024-01-01T00:00:00",
            level="info",
            category="test",
            message="test message",
            data={"key": "value"},
        )

        assert entry.correlation_id == "test-id"
        assert entry.timestamp == "2024-01-01T00:00:00"
        assert entry.level == "info"
        assert entry.category == "test"
        assert entry.message == "test message"
        assert entry.data == {"key": "value"}

    def test_ai_interaction_creation(self):
        interaction = AIInteraction(
            correlation_id="test-id",
            timestamp="2024-01-01T00:00:00",
            prompt="test prompt",
            response="test response",
            token_count=100,
            allowed_tools=["tool1"],
            duration_ms=500.0,
        )

        assert interaction.prompt == "test prompt"
        assert interaction.response == "test response"
        assert interaction.token_count == 100
        assert interaction.allowed_tools == ["tool1"]
        assert interaction.duration_ms == 500.0

    def test_context_gathering_creation(self):
        context = ContextGathering(
            correlation_id="test-id",
            timestamp="2024-01-01T00:00:00",
            files_analyzed=["file1.py"],
            patterns_detected=["pattern1"],
            decisions_made={"key": "value"},
        )

        assert context.files_analyzed == ["file1.py"]
        assert context.patterns_detected == ["pattern1"]
        assert context.decisions_made == {"key": "value"}

    def test_performance_metrics_creation(self):
        metrics = PerformanceMetrics(
            correlation_id="test-id",
            timestamp="2024-01-01T00:00:00",
            operation="test_op",
            duration_ms=250.0,
            phase="test_phase",
        )

        assert metrics.operation == "test_op"
        assert metrics.duration_ms == 250.0
        assert metrics.phase == "test_phase"

    def test_claude_operation_success_logging(self):
        """Test that the error boundary logs start and success messages automatically."""
        service = ClaudeDiagnostics(level="info")

        with service.claude_operation(
            operation_name="test_operation",
            error_code="test_error",
            error_message="Test failed",
        ):
            # Simulate some work
            pass

        # Should have 2 entries: start and success
        assert len(service.entries) == 2

        start_entry = service.entries[0]
        assert start_entry.level == "info"
        assert start_entry.category == "test_operation_start"
        assert start_entry.message == "Starting test_operation"

        success_entry = service.entries[1]
        assert success_entry.level == "info"
        assert success_entry.category == "test_operation_success"
        assert success_entry.message == "Successfully completed test_operation"
        assert "duration_ms" in success_entry.data

    def test_claude_operation_error_logging(self):
        """Test that the error boundary logs errors when exceptions occur."""
        service = ClaudeDiagnostics(level="info")

        try:
            with service.claude_operation(
                operation_name="failing_operation",
                error_code="operation_failed",
                error_message="Operation failed with error",
            ):
                raise ValueError("Test error")
        except ValueError:
            pass  # Expected

        # Should have 2 entries: start and error (no success)
        assert len(service.entries) == 2

        start_entry = service.entries[0]
        assert start_entry.level == "info"
        assert start_entry.category == "failing_operation_start"
        assert start_entry.message == "Starting failing_operation"

        error_entry = service.entries[1]
        assert error_entry.level == "error"
        assert error_entry.category == "operation_failed"
        assert error_entry.message == "Operation failed with error"
        assert error_entry.data["error_type"] == "ValueError"
        assert error_entry.data["error_message"] == "Test error"
        assert "duration_ms" in error_entry.data
