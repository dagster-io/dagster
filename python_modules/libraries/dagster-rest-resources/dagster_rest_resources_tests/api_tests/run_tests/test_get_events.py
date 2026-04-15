"""Test run get-events business logic functions and CLI command invocation.

These tests cover the formatting, filtering, and pagination logic for
`dg api run get-events`, consolidated from the former log_tests and run_event_tests.
"""

import json
from unittest.mock import MagicMock

from dagster_rest_resources.graphql_adapter import run_event as mod
from dagster_rest_resources.graphql_adapter.run_event import (
    _filter_events_by_level,
    _filter_events_by_step,
    _filter_events_by_type,
    get_run_events_via_graphql,
)
from dagster_rest_resources.schemas.run_event import (
    DgApiErrorInfo,
    DgApiRunEvent,
    RunEventLevel,
    RunEventList,
)


class TestLogDataProcessing:
    """Test processing of log data structures.

    This class tests the data model creation and processing logic
    for run events and error information.
    """

    def test_error_info_stack_trace_formatting(self):
        """Test DgApiErrorInfo stack trace string conversion."""
        error = DgApiErrorInfo(
            message="Test error message",
            className="TestError",
            stack=[
                '  File "/app/test.py", line 10, in test_function\n    raise TestError("Something went wrong")\n',
                '  File "/app/main.py", line 5, in main\n    test_function()\n',
            ],
            cause=None,
        )

        stack_trace = error.get_stack_trace_string()
        expected = (
            '  File "/app/test.py", line 10, in test_function\n'
            '    raise TestError("Something went wrong")\n\n'
            '  File "/app/main.py", line 5, in main\n'
            "    test_function()\n"
        )

        assert stack_trace == expected

    def test_error_info_empty_stack(self):
        """Test DgApiErrorInfo with empty stack."""
        error = DgApiErrorInfo(
            message="Error with no stack",
            className="EmptyStackError",
            stack=None,
            cause=None,
        )

        assert error.get_stack_trace_string() == ""

        # Test with empty list too
        error_empty_list = DgApiErrorInfo(
            message="Error with empty stack list",
            className="EmptyStackError",
            stack=[],
            cause=None,
        )

        assert error_empty_list.get_stack_trace_string() == ""

    def test_run_event_creation_with_all_levels(self, snapshot):
        """Test creating run events with all possible log levels."""
        events = [
            DgApiRunEvent(
                run_id=f"level-{level.value.lower()}-run",
                message=f"Message at {level.value} level",
                timestamp="1641046800000",
                level=level,
                step_key=f"step_{level.value.lower()}" if level != RunEventLevel.INFO else None,
                event_type="MessageEvent",
                error=None,
            )
            for level in RunEventLevel
        ]

        log_list = RunEventList(items=events, total=len(events))

        # Test JSON serialization works correctly for all levels
        result = log_list.model_dump_json(indent=2)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_run_event_list_pagination_handling(self):
        """Test RunEventList pagination properties."""
        events = [
            DgApiRunEvent(
                run_id=f"pagination-run-{i}",
                message=f"Message {i}",
                timestamp=f"164104680{i}000",
                level=RunEventLevel.INFO,
                step_key=None,
                event_type="MessageEvent",
                error=None,
            )
            for i in range(3)
        ]

        # Test with pagination info
        log_list = RunEventList(
            items=events,
            total=10,  # Total could be different from items length (pagination)
            cursor="next_page_cursor",
            has_more=True,
        )

        assert len(log_list.items) == 3
        assert log_list.total == 10
        assert log_list.cursor == "next_page_cursor"
        assert log_list.has_more is True

    def test_nested_error_cause_chain(self):
        """Test deeply nested error cause chains."""
        # Create a 3-level deep error chain
        root_error = DgApiErrorInfo(
            message="IOError: File not found",
            className="IOError",
            stack=[
                "  File \"/app/io.py\", line 15, in read_file\n    with open(filename, 'r') as f:\n"
            ],
            cause=None,
        )

        middle_error = DgApiErrorInfo(
            message="ProcessingError: Failed to process file",
            className="ProcessingError",
            stack=[
                '  File "/app/processor.py", line 25, in process\n    content = read_file(filename)\n'
            ],
            cause=root_error,
        )

        top_error = DgApiErrorInfo(
            message="PipelineError: Pipeline execution failed",
            className="PipelineError",
            stack=[
                '  File "/app/pipeline.py", line 50, in run\n    result = process(input_file)\n'
            ],
            cause=middle_error,
        )

        # Verify the chain is properly constructed
        assert top_error.cause is middle_error
        assert middle_error.cause is root_error
        assert root_error.cause is None

        # Test stack trace formatting works for all levels
        assert "Pipeline execution failed" in top_error.message
        assert top_error.cause is not None
        assert "Failed to process file" in top_error.cause.message
        assert top_error.cause.cause is not None
        assert "File not found" in top_error.cause.cause.message

    def test_run_event_with_no_optional_fields(self):
        """Test DgApiRunEvent creation with minimal required fields."""
        event = DgApiRunEvent(
            run_id="minimal-run",
            message="Minimal event",
            timestamp="1641046800000",
            level=RunEventLevel.INFO,
            # All optional fields are None by default
        )

        assert event.run_id == "minimal-run"
        assert event.message == "Minimal event"
        assert event.timestamp == "1641046800000"
        assert event.level == RunEventLevel.INFO
        assert event.step_key is None
        assert event.event_type is None
        assert event.error is None


SAMPLE_EVENTS = [
    {"eventType": "PIPELINE_START", "level": "INFO", "stepKey": None, "message": "run started"},
    {"eventType": "STEP_START", "level": "DEBUG", "stepKey": "my_step", "message": "step started"},
    {"eventType": "STEP_OUTPUT", "level": "DEBUG", "stepKey": "my_step", "message": "output"},
    {"eventType": "STEP_FAILURE", "level": "ERROR", "stepKey": "my_step", "message": "step failed"},
    {
        "eventType": "PIPELINE_FAILURE",
        "level": "ERROR",
        "stepKey": None,
        "message": "run failed",
    },
    {
        "eventType": "STEP_START",
        "level": "DEBUG",
        "stepKey": "other_step",
        "message": "other started",
    },
    {
        "eventType": "STEP_SUCCESS",
        "level": "DEBUG",
        "stepKey": "other_step",
        "message": "other done",
    },
]


class TestFilterEventsByLevel:
    def test_empty_levels_returns_all(self):
        assert _filter_events_by_level(SAMPLE_EVENTS, ()) == SAMPLE_EVENTS

    def test_single_level(self):
        result = _filter_events_by_level(SAMPLE_EVENTS, ("ERROR",))
        assert len(result) == 2
        assert all(e["level"] == "ERROR" for e in result)

    def test_multiple_levels(self):
        result = _filter_events_by_level(SAMPLE_EVENTS, ("ERROR", "INFO"))
        assert len(result) == 3
        assert {e["level"] for e in result} == {"ERROR", "INFO"}

    def test_case_insensitive(self):
        result = _filter_events_by_level(SAMPLE_EVENTS, ("error",))
        assert len(result) == 2


class TestFilterEventsByType:
    def test_empty_types_returns_all(self):
        assert _filter_events_by_type(SAMPLE_EVENTS, ()) == SAMPLE_EVENTS

    def test_single_type(self):
        result = _filter_events_by_type(SAMPLE_EVENTS, ("STEP_FAILURE",))
        assert len(result) == 1
        assert result[0]["eventType"] == "STEP_FAILURE"

    def test_multiple_types(self):
        result = _filter_events_by_type(SAMPLE_EVENTS, ("STEP_START", "STEP_SUCCESS"))
        assert len(result) == 3

    def test_case_insensitive(self):
        result = _filter_events_by_type(SAMPLE_EVENTS, ("step_failure",))
        assert len(result) == 1

    def test_run_start_alias_matches_pipeline_start(self):
        """RUN_START should match events with eventType PIPELINE_START."""
        result = _filter_events_by_type(SAMPLE_EVENTS, ("RUN_START",))
        assert len(result) == 1
        assert result[0]["eventType"] == "PIPELINE_START"

    def test_pipeline_start_also_works(self):
        """PIPELINE_START should still match directly."""
        result = _filter_events_by_type(SAMPLE_EVENTS, ("PIPELINE_START",))
        assert len(result) == 1
        assert result[0]["eventType"] == "PIPELINE_START"

    def test_run_failure_alias_matches_pipeline_failure(self):
        """RUN_FAILURE should match events with eventType PIPELINE_FAILURE."""
        result = _filter_events_by_type(SAMPLE_EVENTS, ("RUN_FAILURE",))
        assert len(result) == 1
        assert result[0]["eventType"] == "PIPELINE_FAILURE"

    def test_mixed_alias_and_direct_types(self):
        """Mix of aliased and direct types should work together."""
        result = _filter_events_by_type(SAMPLE_EVENTS, ("RUN_START", "STEP_FAILURE"))
        assert len(result) == 2
        event_types = {e["eventType"] for e in result}
        assert event_types == {"PIPELINE_START", "STEP_FAILURE"}


class TestFilterEventsByStep:
    def test_empty_keys_returns_all(self):
        assert _filter_events_by_step(SAMPLE_EVENTS, ()) == SAMPLE_EVENTS

    def test_single_key_partial_match(self):
        result = _filter_events_by_step(SAMPLE_EVENTS, ("my_step",))
        assert len(result) == 3
        assert all(e["stepKey"] == "my_step" for e in result)

    def test_multiple_keys(self):
        result = _filter_events_by_step(SAMPLE_EVENTS, ("my_step", "other_step"))
        assert len(result) == 5

    def test_partial_match(self):
        result = _filter_events_by_step(SAMPLE_EVENTS, ("other",))
        assert len(result) == 2


def _make_page(events, cursor, has_more):
    return {
        "logsForRun": {
            "__typename": "EventConnection",
            "events": events,
            "cursor": cursor,
            "hasMore": has_more,
        }
    }


class TestAutoPagination:
    def test_no_filters_single_page(self):
        """Without filters, only one page is fetched."""
        client = MagicMock()
        client.execute.return_value = _make_page(SAMPLE_EVENTS[:3], "c1", True)

        result = get_run_events_via_graphql(client, run_id="r1", limit=100)
        assert len(result["events"]) == 3
        assert result["hasMore"] is True
        assert client.execute.call_count == 1

    def test_filter_triggers_pagination(self):
        """With filters, pages are fetched until limit is reached."""
        client = MagicMock()
        # Page 1: no ERROR events
        page1_events = [
            {"eventType": "STEP_START", "level": "DEBUG", "stepKey": "s1", "message": "a"},
            {"eventType": "STEP_OUTPUT", "level": "DEBUG", "stepKey": "s1", "message": "b"},
        ]
        # Page 2: has ERROR events
        page2_events = [
            {"eventType": "STEP_FAILURE", "level": "ERROR", "stepKey": "s1", "message": "fail"},
        ]
        client.execute.side_effect = [
            _make_page(page1_events, "c1", True),
            _make_page(page2_events, "c2", False),
        ]

        result = get_run_events_via_graphql(client, run_id="r1", limit=100, levels=("ERROR",))
        assert len(result["events"]) == 1
        assert result["events"][0]["level"] == "ERROR"
        assert result["hasMore"] is False
        assert client.execute.call_count == 2

    def test_pagination_respects_limit(self):
        """Auto-pagination stops once limit matching events are collected."""
        client = MagicMock()
        error_event = {
            "eventType": "STEP_FAILURE",
            "level": "ERROR",
            "stepKey": "s1",
            "message": "err",
        }
        # Each page returns 1 matching event, server always has more
        client.execute.side_effect = [_make_page([error_event], f"c{i}", True) for i in range(5)]

        result = get_run_events_via_graphql(client, run_id="r1", limit=3, levels=("ERROR",))
        assert len(result["events"]) == 3
        assert result["hasMore"] is True
        assert client.execute.call_count == 3

    def test_pagination_max_pages_cap(self):
        """Auto-pagination stops at _MAX_PAGES even if limit not reached."""
        client = MagicMock()
        # Every page returns no matching events but has more
        no_match = [
            {"eventType": "PIPELINE_START", "level": "INFO", "stepKey": None, "message": "x"}
        ]
        client.execute.return_value = _make_page(no_match, "cursor", True)

        original = mod._MAX_PAGES  # noqa: SLF001
        mod._MAX_PAGES = 5  # lower cap for test speed  # noqa: SLF001
        try:
            result = get_run_events_via_graphql(client, run_id="r1", limit=100, levels=("ERROR",))
            assert len(result["events"]) == 0
            assert client.execute.call_count == 5
        finally:
            mod._MAX_PAGES = original  # noqa: SLF001


_RUN_ID = "a34cd75c-cfa9-4e99-8f0a-955492b89afd"

_SAMPLE_GRAPHQL_RESPONSE = {
    "logsForRun": {
        "__typename": "EventConnection",
        "events": [
            {
                "__typename": "MessageEvent",
                "runId": _RUN_ID,
                "message": 'Started execution of run for "dbt_analytics_core_job".',
                "timestamp": "1771476078297",
                "level": "INFO",
                "stepKey": None,
                "eventType": "PIPELINE_START",
            },
            {
                "__typename": "MessageEvent",
                "runId": _RUN_ID,
                "message": 'dbt_analytics_core_job intends to materialize asset "my_asset".',
                "timestamp": "1771476078298",
                "level": "INFO",
                "stepKey": "dbt_non_partitioned_models_2",
                "eventType": "ASSET_MATERIALIZATION_PLANNED",
            },
        ],
        "cursor": None,
        "hasMore": False,
    }
}
