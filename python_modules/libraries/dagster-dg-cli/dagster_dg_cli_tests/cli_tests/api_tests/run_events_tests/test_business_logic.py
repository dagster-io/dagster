"""Test run events business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_dg_cli.api_layer.schemas.run_event import (
    DgApiRunEvent,
    DgApiRunEventLevel,
    DgApiRunEventList,
)
from dagster_dg_cli.cli.api.run_event import format_run_events_json, format_run_events_table


class TestFormatRunEvents:
    """Test the run events formatting functions."""

    def _create_sample_event_list(self):
        """Create sample RunEventList for testing."""
        events = [
            DgApiRunEvent(
                run_id="123e4567-e89b-12d3-a456-426614174000",
                message="Run started",
                timestamp="2024-01-15T10:30:00Z",
                level=DgApiRunEventLevel.INFO,
                step_key=None,
                event_type="RUN_START",
            ),
            DgApiRunEvent(
                run_id="123e4567-e89b-12d3-a456-426614174000",
                message="Step my_step started",
                timestamp="2024-01-15T10:31:00Z",
                level=DgApiRunEventLevel.INFO,
                step_key="my_step",
                event_type="STEP_START",
            ),
            DgApiRunEvent(
                run_id="123e4567-e89b-12d3-a456-426614174000",
                message="Step completed successfully with output 42",
                timestamp="2024-01-15T10:32:00Z",
                level=DgApiRunEventLevel.INFO,
                step_key="my_step",
                event_type="STEP_SUCCESS",
            ),
            DgApiRunEvent(
                run_id="123e4567-e89b-12d3-a456-426614174000",
                message="Run completed successfully",
                timestamp="2024-01-15T10:33:00Z",
                level=DgApiRunEventLevel.INFO,
                step_key=None,
                event_type="RUN_SUCCESS",
            ),
        ]
        return DgApiRunEventList(items=events, total=len(events))

    def _create_empty_event_list(self):
        """Create empty RunEventList for testing."""
        return DgApiRunEventList(items=[], total=0)

    def _create_error_event_list(self):
        """Create RunEventList with error events for testing."""
        events = [
            DgApiRunEvent(
                run_id="failed-run-456",
                message="Run started",
                timestamp="2024-01-15T10:30:00Z",
                level=DgApiRunEventLevel.INFO,
                step_key=None,
                event_type="RUN_START",
            ),
            DgApiRunEvent(
                run_id="failed-run-456",
                message="Step my_step started",
                timestamp="2024-01-15T10:31:00Z",
                level=DgApiRunEventLevel.INFO,
                step_key="my_step",
                event_type="STEP_START",
            ),
            DgApiRunEvent(
                run_id="failed-run-456",
                message="Step failed with error: Division by zero",
                timestamp="2024-01-15T10:32:00Z",
                level=DgApiRunEventLevel.ERROR,
                step_key="my_step",
                event_type="STEP_FAILURE",
            ),
            DgApiRunEvent(
                run_id="failed-run-456",
                message="Run failed due to step failure",
                timestamp="2024-01-15T10:33:00Z",
                level=DgApiRunEventLevel.ERROR,
                step_key=None,
                event_type="RUN_FAILURE",
            ),
        ]
        return DgApiRunEventList(items=events, total=len(events))

    def test_format_run_events_text_output(self, snapshot):
        """Test formatting run events as text."""
        events = self._create_sample_event_list()
        result = format_run_events_table(events, "123e4567-e89b-12d3-a456-426614174000")

        # Snapshot the entire text output
        snapshot.assert_match(result)

    def test_format_run_events_json_output(self, snapshot):
        """Test formatting run events as JSON."""
        events = self._create_sample_event_list()
        result = format_run_events_json(events, "123e4567-e89b-12d3-a456-426614174000")

        # For JSON, we want to snapshot the parsed structure to avoid formatting differences
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_empty_run_events_text_output(self, snapshot):
        """Test formatting empty run events as text."""
        events = self._create_empty_event_list()
        result = format_run_events_table(events, "123e4567-e89b-12d3-a456-426614174000")

        snapshot.assert_match(result)

    def test_format_empty_run_events_json_output(self, snapshot):
        """Test formatting empty run events as JSON."""
        events = self._create_empty_event_list()
        result = format_run_events_json(events, "123e4567-e89b-12d3-a456-426614174000")

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_error_events_text_output(self, snapshot):
        """Test formatting error events as text."""
        events = self._create_error_event_list()
        result = format_run_events_table(events, "failed-run-456")

        snapshot.assert_match(result)

    def test_format_error_events_json_output(self, snapshot):
        """Test formatting error events as JSON."""
        events = self._create_error_event_list()
        result = format_run_events_json(events, "failed-run-456")

        parsed = json.loads(result)
        snapshot.assert_match(parsed)


class TestRunEventDataProcessing:
    """Test processing of run event data structures.

    This class would test any pure functions in the GraphQL adapter
    that process the raw GraphQL responses into our domain models.
    """

    def test_run_event_creation_with_all_fields(self, snapshot):
        """Test creating run event with all possible fields."""
        event = DgApiRunEvent(
            run_id="complete-event-xyz",
            message="This is a comprehensive test event with all fields populated",
            timestamp="2024-01-15T10:30:00Z",
            level=DgApiRunEventLevel.WARNING,
            step_key="comprehensive_step",
            event_type="STEP_MATERIALIZATION",
        )

        # Test JSON serialization works correctly
        result = event.model_dump_json(indent=2)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_run_event_level_enum_values(self):
        """Test that all expected RunEventLevel enum values are available."""
        expected_levels = [
            "CRITICAL",
            "ERROR",
            "WARNING",
            "INFO",
            "DEBUG",
        ]

        actual_levels = [level.value for level in DgApiRunEventLevel]
        assert set(actual_levels) == set(expected_levels)

    def test_run_event_with_missing_optional_fields(self):
        """Test run event creation with None values for optional fields."""
        event = DgApiRunEvent(
            run_id="sparse-event-123",
            message="Simple event with minimal fields",
            timestamp="2024-01-15T10:30:00Z",
            level=DgApiRunEventLevel.INFO,
            step_key=None,
            event_type="RUN_START",
        )

        assert event.run_id == "sparse-event-123"
        assert event.message == "Simple event with minimal fields"
        assert event.timestamp == "2024-01-15T10:30:00Z"
        assert event.level == DgApiRunEventLevel.INFO
        assert event.step_key is None
        assert event.event_type == "RUN_START"

    def test_run_event_list_creation(self):
        """Test creating RunEventList with events."""
        events = [
            DgApiRunEvent(
                run_id="list-test-123",
                message="First event",
                timestamp="2024-01-15T10:30:00Z",
                level=DgApiRunEventLevel.INFO,
                event_type="RUN_START",
            ),
            DgApiRunEvent(
                run_id="list-test-123",
                message="Second event",
                timestamp="2024-01-15T10:31:00Z",
                level=DgApiRunEventLevel.INFO,
                event_type="RUN_SUCCESS",
            ),
        ]

        event_list = DgApiRunEventList(
            items=events,
            total=len(events),
            cursor="next_cursor",
            has_more=True,
        )

        assert len(event_list.items) == 2
        assert event_list.total == 2
        assert event_list.cursor == "next_cursor"
        assert event_list.has_more is True

    def test_run_event_level_string_values(self):
        """Test specific string values of event levels."""
        assert DgApiRunEventLevel.CRITICAL.value == "CRITICAL"
        assert DgApiRunEventLevel.ERROR.value == "ERROR"
        assert DgApiRunEventLevel.WARNING.value == "WARNING"
        assert DgApiRunEventLevel.INFO.value == "INFO"
        assert DgApiRunEventLevel.DEBUG.value == "DEBUG"
