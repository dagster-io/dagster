"""Test run event schema models in isolation.

These tests verify the basic data models work correctly without
importing any CLI or GraphQL components that might have import issues.
"""

import json

from dagster_dg_cli.api_layer.schemas.run_event import (
    DgApiRunEvent,
    DgApiRunEventLevel,
    DgApiRunEventList,
)


class TestRunEventSchema:
    """Test the RunEvent schema model."""

    def test_run_event_creation_minimal(self):
        """Test creating run event with required fields."""
        event = DgApiRunEvent(
            run_id="test-run-123",
            message="Test event message",
            timestamp="2024-01-15T10:30:00Z",
            level=DgApiRunEventLevel.INFO,
            event_type="RUN_START",
        )

        assert event.run_id == "test-run-123"
        assert event.message == "Test event message"
        assert event.timestamp == "2024-01-15T10:30:00Z"
        assert event.level == DgApiRunEventLevel.INFO
        assert event.step_key is None
        assert event.event_type == "RUN_START"

    def test_run_event_creation_complete(self):
        """Test creating run event with all fields."""
        event = DgApiRunEvent(
            run_id="complete-event-456",
            message="Complete event with step",
            timestamp="2024-01-15T10:30:00Z",
            level=DgApiRunEventLevel.WARNING,
            step_key="my_step",
            event_type="STEP_MATERIALIZATION",
        )

        assert event.run_id == "complete-event-456"
        assert event.message == "Complete event with step"
        assert event.timestamp == "2024-01-15T10:30:00Z"
        assert event.level == DgApiRunEventLevel.WARNING
        assert event.step_key == "my_step"
        assert event.event_type == "STEP_MATERIALIZATION"

    def test_run_event_json_serialization(self):
        """Test that RunEvent can be serialized to JSON."""
        event = DgApiRunEvent(
            run_id="json-test-789",
            message="JSON serialization test",
            timestamp="2024-01-15T10:30:00Z",
            level=DgApiRunEventLevel.ERROR,
            step_key="error_step",
            event_type="STEP_FAILURE",
        )

        json_str = event.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["run_id"] == "json-test-789"
        assert parsed["message"] == "JSON serialization test"
        assert parsed["timestamp"] == "2024-01-15T10:30:00Z"
        assert parsed["level"] == "ERROR"
        assert parsed["step_key"] == "error_step"
        assert parsed["event_type"] == "STEP_FAILURE"

    def test_run_event_json_deserialization(self):
        """Test that RunEvent can be created from JSON."""
        json_data = {
            "run_id": "from-json-abc",
            "message": "Event from JSON",
            "timestamp": "2024-01-15T10:30:00Z",
            "level": "DEBUG",
            "step_key": "debug_step",
            "event_type": "STEP_OUTPUT",
        }

        event = DgApiRunEvent(**json_data)  # type: ignore

        assert event.run_id == "from-json-abc"
        assert event.message == "Event from JSON"
        assert event.timestamp == "2024-01-15T10:30:00Z"
        assert event.level == DgApiRunEventLevel.DEBUG
        assert event.step_key == "debug_step"
        assert event.event_type == "STEP_OUTPUT"


class TestRunEventListSchema:
    """Test the RunEventList schema model."""

    def test_run_event_list_creation_empty(self):
        """Test creating empty RunEventList."""
        event_list = DgApiRunEventList(items=[], total=0)

        assert len(event_list.items) == 0
        assert event_list.total == 0
        assert event_list.cursor is None
        assert event_list.has_more is False

    def test_run_event_list_creation_with_events(self):
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
            total=2,
            cursor="next_page_cursor",
            has_more=True,
        )

        assert len(event_list.items) == 2
        assert event_list.total == 2
        assert event_list.cursor == "next_page_cursor"
        assert event_list.has_more is True

    def test_run_event_list_json_serialization(self):
        """Test that RunEventList can be serialized to JSON."""
        events = [
            DgApiRunEvent(
                run_id="json-list-test",
                message="Event in list",
                timestamp="2024-01-15T10:30:00Z",
                level=DgApiRunEventLevel.INFO,
                event_type="RUN_START",
            )
        ]

        event_list = DgApiRunEventList(items=events, total=1, has_more=False)
        json_str = event_list.model_dump_json()
        parsed = json.loads(json_str)

        assert len(parsed["items"]) == 1
        assert parsed["total"] == 1
        assert parsed["has_more"] is False
        assert parsed["items"][0]["run_id"] == "json-list-test"


class TestRunEventLevelEnum:
    """Test the RunEventLevel enum."""

    def test_run_event_level_values(self):
        """Test that all expected RunEventLevel values are available."""
        expected_levels = [
            "CRITICAL",
            "ERROR",
            "WARNING",
            "INFO",
            "DEBUG",
        ]

        actual_levels = [level.value for level in DgApiRunEventLevel]
        assert set(actual_levels) == set(expected_levels)

    def test_run_event_level_enum_creation(self):
        """Test creating events with each level value."""
        for level in DgApiRunEventLevel:
            event = DgApiRunEvent(
                run_id=f"test-{level.value.lower()}",
                message=f"Test message for {level.value}",
                timestamp="2024-01-15T10:30:00Z",
                level=level,
                event_type="TEST_EVENT",
            )
            assert event.level == level

    def test_run_event_level_string_values(self):
        """Test specific string values of event levels."""
        assert DgApiRunEventLevel.CRITICAL.value == "CRITICAL"
        assert DgApiRunEventLevel.ERROR.value == "ERROR"
        assert DgApiRunEventLevel.WARNING.value == "WARNING"
        assert DgApiRunEventLevel.INFO.value == "INFO"
        assert DgApiRunEventLevel.DEBUG.value == "DEBUG"
