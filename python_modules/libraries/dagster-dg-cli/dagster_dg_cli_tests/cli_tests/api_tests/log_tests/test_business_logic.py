"""Test log business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

from unittest.mock import MagicMock

from dagster_dg_cli.api_layer.graphql_adapter.run_event import (
    _filter_events_by_level,
    _filter_events_by_step,
    _filter_events_by_type,
    get_run_events_via_graphql,
)
from dagster_dg_cli.api_layer.schemas.run_event import (
    DgApiErrorInfo,
    DgApiRunEvent,
    RunEventLevel,
    RunEventList,
)
from dagster_dg_cli.cli.api.log import format_logs_json, format_logs_table


class TestFormatLogs:
    """Test the log formatting functions."""

    def _create_sample_log_list(self):
        """Create sample RunEventList for testing."""
        events = [
            DgApiRunEvent(
                run_id="test-run-12345",
                message='Starting execution of run for "test_pipeline".',
                timestamp="1641046800000",  # 2022-01-01 14:20:00 UTC (as milliseconds)
                level=RunEventLevel.INFO,
                step_key=None,
                event_type="RunStartEvent",
                error=None,
            ),
            DgApiRunEvent(
                run_id="test-run-12345",
                message='Started execution of step "process_data".',
                timestamp="1641046805000",  # 2022-01-01 14:20:05 UTC
                level=RunEventLevel.DEBUG,
                step_key="process_data",
                event_type="ExecutionStepStartEvent",
                error=None,
            ),
            DgApiRunEvent(
                run_id="test-run-12345",
                message="Loading input from path: /tmp/input.json",
                timestamp="1641046810000",  # 2022-01-01 14:20:10 UTC
                level=RunEventLevel.DEBUG,
                step_key="process_data",
                event_type="MessageEvent",
                error=None,
            ),
            DgApiRunEvent(
                run_id="test-run-12345",
                message='Execution of step "process_data" failed.',
                timestamp="1641046815000",  # 2022-01-01 14:20:15 UTC
                level=RunEventLevel.ERROR,
                step_key="process_data",
                event_type="ExecutionStepFailureEvent",
                error=DgApiErrorInfo(
                    message="ValueError: Invalid input data format\n",
                    className="ValueError",
                    stack=[
                        '  File "/app/pipeline.py", line 42, in process_data\n    data = json.loads(input_str)\n',
                        '  File "/usr/lib/python3.12/json/__init__.py", line 346, in loads\n    return _default_decoder.decode(s)\n',
                        '  File "/usr/lib/python3.12/json/decoder.py", line 337, in decode\n    obj, end = self.raw_decode(s, idx=_w(s, 0).end())\n',
                    ],
                    cause=None,
                ),
            ),
            DgApiRunEvent(
                run_id="test-run-12345",
                message="Execution of run for \"test_pipeline\" failed. Steps failed: ['process_data'].",
                timestamp="1641046820000",  # 2022-01-01 14:20:20 UTC
                level=RunEventLevel.ERROR,
                step_key=None,
                event_type="RunFailureEvent",
                error=None,
            ),
        ]
        return RunEventList(items=events, total=5, cursor=None, has_more=False)

    def _create_empty_log_list(self):
        """Create empty RunEventList for testing."""
        return RunEventList(items=[], total=0, cursor=None, has_more=False)

    def _create_log_with_nested_error(self):
        """Create log with nested error causes."""
        return DgApiRunEvent(
            run_id="nested-error-run",
            message="Database connection failed with retry exhausted.",
            timestamp="1641046825000",
            level=RunEventLevel.ERROR,
            step_key="database_query",
            event_type="ExecutionStepFailureEvent",
            error=DgApiErrorInfo(
                message="RetryRequestedFromPolicy: Exceeded max_retries of 3\n",
                className="RetryRequestedFromPolicy",
                stack=[
                    '  File "/app/database.py", line 25, in execute_query\n    return self._execute_with_retry(query)\n',
                    '  File "/app/database.py", line 45, in _execute_with_retry\n    raise RetryRequestedFromPolicy(f"Exceeded max_retries of {max_retries}")\n',
                ],
                cause=DgApiErrorInfo(
                    message="ConnectionError: [Errno 111] Connection refused\n",
                    className="ConnectionError",
                    stack=[
                        '  File "/app/database.py", line 35, in _execute_with_retry\n    result = self.connection.execute(query)\n',
                        '  File "/usr/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1418, in execute\n    return connection.execute(statement, parameters)\n',
                        '  File "/usr/lib/python3.12/site-packages/psycopg2/__init__.py", line 122, in connect\n    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)\n',
                    ],
                    cause=None,
                ),
            ),
        )

    def _create_log_with_very_long_step_key(self):
        """Create log with very long step key to test truncation."""
        return DgApiRunEvent(
            run_id="truncation-test-run",
            message="Processing large dataset chunk.",
            timestamp="1641046830000",
            level=RunEventLevel.INFO,
            step_key="very_long_step_name_that_exceeds_the_display_limit_and_should_be_truncated",
            event_type="MessageEvent",
            error=None,
        )

    def test_format_logs_table_output(self, snapshot):
        """Test formatting logs as text table."""
        from dagster_shared.utils.timing import fixed_timezone

        log_list = self._create_sample_log_list()
        with fixed_timezone("UTC"):
            result = format_logs_table(log_list, "test-run-12345")

        # Snapshot the entire text output
        snapshot.assert_match(result)

    def test_format_logs_json_output(self, snapshot):
        """Test formatting logs as JSON."""
        log_list = self._create_sample_log_list()
        result = format_logs_json(log_list, "test-run-12345")

        # For JSON, we want to snapshot the parsed structure to avoid formatting differences
        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_empty_logs_table_output(self, snapshot):
        """Test formatting empty log list as text."""
        log_list = self._create_empty_log_list()
        result = format_logs_table(log_list, "empty-run-67890")

        snapshot.assert_match(result)

    def test_format_empty_logs_json_output(self, snapshot):
        """Test formatting empty log list as JSON."""
        log_list = self._create_empty_log_list()
        result = format_logs_json(log_list, "empty-run-67890")

        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_logs_with_nested_errors(self, snapshot):
        """Test formatting logs with nested error causes."""
        from dagster_shared.utils.timing import fixed_timezone

        log_with_nested_error = self._create_log_with_nested_error()
        log_list = RunEventList(items=[log_with_nested_error], total=1)

        with fixed_timezone("UTC"):
            result = format_logs_table(log_list, "nested-error-run")

        snapshot.assert_match(result)

    def test_format_logs_with_nested_errors_json(self, snapshot):
        """Test formatting logs with nested errors as JSON."""
        log_with_nested_error = self._create_log_with_nested_error()
        log_list = RunEventList(items=[log_with_nested_error], total=1)

        result = format_logs_json(log_list, "nested-error-run")

        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_logs_with_long_step_key(self, snapshot):
        """Test formatting logs with step key truncation."""
        from dagster_shared.utils.timing import fixed_timezone

        log_with_long_key = self._create_log_with_very_long_step_key()
        log_list = RunEventList(items=[log_with_long_key], total=1)

        with fixed_timezone("UTC"):
            result = format_logs_table(log_list, "truncation-test-run")

        snapshot.assert_match(result)

    def test_format_logs_with_pagination_info(self, snapshot):
        """Test formatting logs with pagination indicators."""
        from dagster_shared.utils.timing import fixed_timezone

        # Create log list that has more data available
        log_list = RunEventList(
            items=[
                DgApiRunEvent(
                    run_id="paginated-run",
                    message="First log entry",
                    timestamp="1641046800000",
                    level=RunEventLevel.INFO,
                    step_key=None,
                    event_type="MessageEvent",
                    error=None,
                ),
                DgApiRunEvent(
                    run_id="paginated-run",
                    message="Second log entry",
                    timestamp="1641046805000",
                    level=RunEventLevel.DEBUG,
                    step_key="step_1",
                    event_type="MessageEvent",
                    error=None,
                ),
            ],
            total=2,
            cursor="cursor_token_12345",
            has_more=True,
        )

        with fixed_timezone("UTC"):
            result = format_logs_table(log_list, "paginated-run")

        snapshot.assert_match(result)

    def test_format_logs_all_levels(self, snapshot):
        """Test formatting logs with all log levels."""
        from dagster_shared.utils.timing import fixed_timezone

        events = [
            DgApiRunEvent(
                run_id="level-test-run",
                message=f"This is a {level.value} level message",
                timestamp="1641046800000",
                level=level,
                step_key="test_step" if level != RunEventLevel.INFO else None,
                event_type="MessageEvent",
                error=None,
            )
            for level in RunEventLevel
        ]

        log_list = RunEventList(items=events, total=len(events))

        with fixed_timezone("UTC"):
            result = format_logs_table(log_list, "level-test-run")

        snapshot.assert_match(result)


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
        import json

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

    def test_timestamp_handling_edge_cases(self, snapshot):
        """Test timestamp formatting with edge case values."""
        from dagster_shared.utils.timing import fixed_timezone

        # Test various timestamp formats
        events = [
            DgApiRunEvent(
                run_id="timestamp-test",
                message="Epoch timestamp",
                timestamp="0",  # Unix epoch
                level=RunEventLevel.INFO,
                step_key=None,
                event_type="MessageEvent",
                error=None,
            ),
            DgApiRunEvent(
                run_id="timestamp-test",
                message="Large timestamp",
                timestamp="32503680000000",  # Year 3000
                level=RunEventLevel.DEBUG,
                step_key=None,
                event_type="MessageEvent",
                error=None,
            ),
        ]

        log_list = RunEventList(items=events, total=len(events))

        with fixed_timezone("UTC"):
            result = format_logs_table(log_list, "timestamp-test")

        snapshot.assert_match(result)


SAMPLE_EVENTS = [
    {"eventType": "RUN_START", "level": "INFO", "stepKey": None, "message": "run started"},
    {"eventType": "STEP_START", "level": "DEBUG", "stepKey": "my_step", "message": "step started"},
    {"eventType": "STEP_OUTPUT", "level": "DEBUG", "stepKey": "my_step", "message": "output"},
    {"eventType": "STEP_FAILURE", "level": "ERROR", "stepKey": "my_step", "message": "step failed"},
    {"eventType": "RUN_FAILURE", "level": "ERROR", "stepKey": None, "message": "run failed"},
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
        from dagster_dg_cli.api_layer.graphql_adapter import run_event as mod

        client = MagicMock()
        # Every page returns no matching events but has more
        no_match = [{"eventType": "RUN_START", "level": "INFO", "stepKey": None, "message": "x"}]
        client.execute.return_value = _make_page(no_match, "cursor", True)

        original = mod._MAX_PAGES  # noqa: SLF001
        mod._MAX_PAGES = 5  # lower cap for test speed  # noqa: SLF001
        try:
            result = get_run_events_via_graphql(client, run_id="r1", limit=100, levels=("ERROR",))
            assert len(result["events"]) == 0
            assert client.execute.call_count == 5
        finally:
            mod._MAX_PAGES = original  # noqa: SLF001
