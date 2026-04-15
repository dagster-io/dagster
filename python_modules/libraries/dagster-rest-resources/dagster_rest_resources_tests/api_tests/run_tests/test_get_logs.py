"""Test run get-logs business logic functions and CLI command invocation.

These tests cover the adapter, formatting, and CLI logic for
`dg api run get-logs`.
"""

from unittest.mock import MagicMock

from dagster_rest_resources.graphql_adapter.compute_log import (
    get_captured_log_content,
    get_captured_log_metadata,
    get_logs_captured_events,
)

_RUN_ID = "b45fff8a-7def-43b8-805d-1cf5f435c997"


def _make_events_page(events, cursor, has_more):
    return {
        "logsForRun": {
            "__typename": "EventConnection",
            "events": events,
            "cursor": cursor,
            "hasMore": has_more,
        }
    }


_SAMPLE_LOGS_CAPTURED_EVENTS = [
    {
        "__typename": "LogsCapturedEvent",
        "fileKey": "my_step",
        "stepKeys": ["my_step"],
        "externalStdoutUrl": None,
        "externalStderrUrl": None,
    },
    {
        "__typename": "LogsCapturedEvent",
        "fileKey": "other_step",
        "stepKeys": ["other_step"],
        "externalStdoutUrl": None,
        "externalStderrUrl": None,
    },
]

_SAMPLE_NON_MATCHING_EVENTS = [
    {
        "__typename": "MessageEvent",
        "runId": _RUN_ID,
        "message": "run started",
        "timestamp": "1641046800000",
        "level": "INFO",
        "stepKey": None,
        "eventType": "PIPELINE_START",
    },
]


class TestGetLogsCapturedEvents:
    """Test the get_logs_captured_events adapter function."""

    def test_filters_to_logs_captured_events_only(self):
        """Only LogsCapturedEvent entries are returned."""
        mixed_events = _SAMPLE_NON_MATCHING_EVENTS + _SAMPLE_LOGS_CAPTURED_EVENTS
        client = MagicMock()
        client.execute.return_value = _make_events_page(mixed_events, None, False)

        result = get_logs_captured_events(client, _RUN_ID)
        assert len(result) == 2
        assert all(e["__typename"] == "LogsCapturedEvent" for e in result)

    def test_step_key_filter(self):
        """step_key parameter filters to events containing that step."""
        client = MagicMock()
        client.execute.return_value = _make_events_page(_SAMPLE_LOGS_CAPTURED_EVENTS, None, False)

        result = get_logs_captured_events(client, _RUN_ID, step_key="my_step")
        assert len(result) == 1
        assert result[0]["fileKey"] == "my_step"

    def test_auto_pagination(self):
        """Events are collected across multiple pages."""
        client = MagicMock()
        client.execute.side_effect = [
            _make_events_page(_SAMPLE_NON_MATCHING_EVENTS, "c1", True),
            _make_events_page(_SAMPLE_LOGS_CAPTURED_EVENTS[:1], "c2", True),
            _make_events_page(_SAMPLE_LOGS_CAPTURED_EVENTS[1:], None, False),
        ]

        result = get_logs_captured_events(client, _RUN_ID)
        assert len(result) == 2
        assert client.execute.call_count == 3

    def test_empty_response(self):
        """Returns empty list when no LogsCapturedEvent found."""
        client = MagicMock()
        client.execute.return_value = _make_events_page(_SAMPLE_NON_MATCHING_EVENTS, None, False)

        result = get_logs_captured_events(client, _RUN_ID)
        assert result == []

    def test_skips_events_without_file_key(self):
        """Events without fileKey are skipped."""
        client = MagicMock()
        event_no_key = {
            "__typename": "LogsCapturedEvent",
            "fileKey": None,
            "stepKeys": [],
            "externalStdoutUrl": None,
            "externalStderrUrl": None,
        }
        client.execute.return_value = _make_events_page([event_no_key], None, False)

        result = get_logs_captured_events(client, _RUN_ID)
        assert result == []

    def test_error_typename_raises(self):
        """Non-EventConnection typename raises an exception."""
        client = MagicMock()
        client.execute.return_value = {
            "logsForRun": {
                "__typename": "RunNotFoundError",
                "message": "Run not found",
            }
        }

        try:
            get_logs_captured_events(client, _RUN_ID)
            assert False, "Should have raised"
        except Exception as e:
            assert "Run not found" in str(e)


class TestGetCapturedLogContent:
    """Test the get_captured_log_content adapter function."""

    def test_returns_content(self):
        """Content is returned from capturedLogs query."""
        client = MagicMock()
        client.execute.return_value = {
            "capturedLogs": {
                "stdout": "hello world\n",
                "stderr": "warning: something\n",
                "cursor": "abc123",
            }
        }

        result = get_captured_log_content(client, [_RUN_ID, "compute_logs", "my_step"])
        assert result["stdout"] == "hello world\n"
        assert result["stderr"] == "warning: something\n"
        assert result["cursor"] == "abc123"

    def test_passes_cursor_and_max_bytes(self):
        """Cursor and max_bytes are passed as variables."""
        client = MagicMock()
        client.execute.return_value = {"capturedLogs": {"stdout": "", "stderr": "", "cursor": None}}

        get_captured_log_content(
            client, [_RUN_ID, "compute_logs", "my_step"], cursor="cur1", max_bytes=1024
        )
        call_args = client.execute.call_args
        variables = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("variables")
        assert variables["cursor"] == "cur1"
        assert variables["limit"] == 1024

    def test_empty_response(self):
        """Returns None values when capturedLogs is empty."""
        client = MagicMock()
        client.execute.return_value = {"capturedLogs": None}

        result = get_captured_log_content(client, [_RUN_ID, "compute_logs", "my_step"])
        assert result["stdout"] is None
        assert result["stderr"] is None


class TestGetCapturedLogMetadata:
    """Test the get_captured_log_metadata adapter function."""

    def test_returns_urls(self):
        """Download URLs are returned from capturedLogsMetadata query."""
        client = MagicMock()
        client.execute.return_value = {
            "capturedLogsMetadata": {
                "stdoutDownloadUrl": "https://example.com/stdout",
                "stderrDownloadUrl": "https://example.com/stderr",
            }
        }

        result = get_captured_log_metadata(client, [_RUN_ID, "compute_logs", "my_step"])
        assert result["stdoutDownloadUrl"] == "https://example.com/stdout"
        assert result["stderrDownloadUrl"] == "https://example.com/stderr"

    def test_empty_response(self):
        """Returns None values when metadata is empty."""
        client = MagicMock()
        client.execute.return_value = {"capturedLogsMetadata": None}

        result = get_captured_log_metadata(client, [_RUN_ID, "compute_logs", "my_step"])
        assert result["stdoutDownloadUrl"] is None
        assert result["stderrDownloadUrl"] is None


# ---------------------------------------------------------------------------
# GraphQL response fixtures for CLI invocation tests
# ---------------------------------------------------------------------------

_SAMPLE_LOGS_CAPTURED_RESPONSE = {
    "logsForRun": {
        "__typename": "EventConnection",
        "events": [
            {
                "__typename": "LogsCapturedEvent",
                "fileKey": "my_step",
                "stepKeys": ["my_step"],
                "externalStdoutUrl": None,
                "externalStderrUrl": None,
            },
        ],
        "cursor": None,
        "hasMore": False,
    }
}

_SAMPLE_CAPTURED_LOGS_RESPONSE = {
    "capturedLogs": {
        "stdout": "hello world\n",
        "stderr": "",
        "cursor": None,
    }
}

_SAMPLE_CAPTURED_LOGS_METADATA_RESPONSE = {
    "capturedLogsMetadata": {
        "stdoutDownloadUrl": "https://storage.example.com/stdout",
        "stderrDownloadUrl": "https://storage.example.com/stderr",
    }
}
