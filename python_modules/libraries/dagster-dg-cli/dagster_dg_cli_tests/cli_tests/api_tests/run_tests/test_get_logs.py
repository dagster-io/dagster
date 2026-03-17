"""Test run get-logs business logic functions and CLI command invocation.

These tests cover the adapter, formatting, and CLI logic for
`dg api run get-logs`.
"""

import json
from unittest.mock import MagicMock

from click.testing import CliRunner
from dagster_dg_cli.api_layer.graphql_adapter.compute_log import (
    get_captured_log_content,
    get_captured_log_metadata,
    get_logs_captured_events,
)
from dagster_dg_cli.api_layer.schemas.compute_log import (
    DgApiComputeLogLinkList,
    DgApiComputeLogList,
    DgApiStepComputeLog,
    DgApiStepComputeLogLink,
)
from dagster_dg_cli.cli.api.client import DgApiTestContext
from dagster_dg_cli.cli.api.formatters import format_compute_log_links, format_compute_logs

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


class TestFormatComputeLogs:
    """Test the compute log formatting functions."""

    def _create_sample_compute_logs(self):
        return DgApiComputeLogList(
            run_id=_RUN_ID,
            items=[
                DgApiStepComputeLog(
                    file_key="my_step",
                    step_keys=["my_step"],
                    stdout="Processing 100 records...\nDone.\n",
                    stderr="WARNING: deprecated API used\n",
                    cursor=None,
                ),
                DgApiStepComputeLog(
                    file_key="other_step",
                    step_keys=["other_step"],
                    stdout="Step completed successfully.\n",
                    stderr=None,
                    cursor=None,
                ),
            ],
            total=2,
        )

    def test_format_compute_logs_table(self, snapshot):
        """Test table formatting of compute logs."""
        logs = self._create_sample_compute_logs()
        result = format_compute_logs(logs, as_json=False)
        snapshot.assert_match(result)

    def test_format_compute_logs_json(self, snapshot):
        """Test JSON formatting of compute logs."""
        logs = self._create_sample_compute_logs()
        result = format_compute_logs(logs, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_empty_compute_logs(self):
        """Test formatting with no logs."""
        logs = DgApiComputeLogList(run_id=_RUN_ID, items=[], total=0)
        result = format_compute_logs(logs, as_json=False)
        assert f"No compute logs found for run {_RUN_ID}" in result

    def test_format_compute_logs_no_output(self, snapshot):
        """Test formatting when step has no stdout or stderr."""
        logs = DgApiComputeLogList(
            run_id=_RUN_ID,
            items=[
                DgApiStepComputeLog(
                    file_key="empty_step",
                    step_keys=["empty_step"],
                    stdout=None,
                    stderr=None,
                    cursor=None,
                ),
            ],
            total=1,
        )
        result = format_compute_logs(logs, as_json=False)
        snapshot.assert_match(result)


class TestFormatComputeLogLinks:
    """Test the compute log links formatting functions."""

    def _create_sample_links(self):
        return DgApiComputeLogLinkList(
            run_id=_RUN_ID,
            items=[
                DgApiStepComputeLogLink(
                    file_key="my_step",
                    step_keys=["my_step"],
                    stdout_download_url="https://storage.example.com/stdout/my_step",
                    stderr_download_url="https://storage.example.com/stderr/my_step",
                ),
                DgApiStepComputeLogLink(
                    file_key="other_step",
                    step_keys=["other_step"],
                    stdout_download_url=None,
                    stderr_download_url=None,
                ),
            ],
            total=2,
        )

    def test_format_links_table(self, snapshot):
        """Test table formatting of compute log links."""
        links = self._create_sample_links()
        result = format_compute_log_links(links, as_json=False)
        snapshot.assert_match(result)

    def test_format_links_json(self, snapshot):
        """Test JSON formatting of compute log links."""
        links = self._create_sample_links()
        result = format_compute_log_links(links, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_empty_links(self):
        """Test formatting with no links."""
        links = DgApiComputeLogLinkList(run_id=_RUN_ID, items=[], total=0)
        result = format_compute_log_links(links, as_json=False)
        assert f"No compute log links found for run {_RUN_ID}" in result


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


class TestGetLogsCommandInvocation:
    """Regression tests for `dg api run get-logs` CLI invocation."""

    def test_command_basic_invocation(self):
        """Basic invocation returns successfully."""
        from dagster_dg_cli.cli import cli as root_cli

        from dagster_dg_cli_tests.cli_tests.api_tests.test_dynamic_command_execution import (
            ReplayClient,
        )

        replay_client = ReplayClient(
            [_SAMPLE_LOGS_CAPTURED_RESPONSE, _SAMPLE_CAPTURED_LOGS_RESPONSE]
        )
        test_context = DgApiTestContext(client_factory=lambda config: replay_client)

        runner = CliRunner()
        result = runner.invoke(root_cli, ["api", "run", "get-logs", _RUN_ID], obj=test_context)

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "my_step" in result.output

    def test_command_link_only(self):
        """--link-only flag uses metadata endpoint."""
        from dagster_dg_cli.cli import cli as root_cli

        from dagster_dg_cli_tests.cli_tests.api_tests.test_dynamic_command_execution import (
            ReplayClient,
        )

        replay_client = ReplayClient(
            [_SAMPLE_LOGS_CAPTURED_RESPONSE, _SAMPLE_CAPTURED_LOGS_METADATA_RESPONSE]
        )
        test_context = DgApiTestContext(client_factory=lambda config: replay_client)

        runner = CliRunner()
        result = runner.invoke(
            root_cli,
            ["api", "run", "get-logs", _RUN_ID, "--link-only"],
            obj=test_context,
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "storage.example.com" in result.output

    def test_command_json_output(self):
        """--json flag returns valid JSON."""
        from dagster_dg_cli.cli import cli as root_cli

        from dagster_dg_cli_tests.cli_tests.api_tests.test_dynamic_command_execution import (
            ReplayClient,
        )

        replay_client = ReplayClient(
            [_SAMPLE_LOGS_CAPTURED_RESPONSE, _SAMPLE_CAPTURED_LOGS_RESPONSE]
        )
        test_context = DgApiTestContext(client_factory=lambda config: replay_client)

        runner = CliRunner()
        result = runner.invoke(
            root_cli,
            ["api", "run", "get-logs", _RUN_ID, "--json"],
            obj=test_context,
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        parsed = json.loads(result.output)
        assert parsed["run_id"] == _RUN_ID
        assert len(parsed["items"]) == 1

    def test_command_accepts_view_graphql_param(self):
        """Regression: get_logs_command must accept view_graphql kwarg."""
        from dagster_dg_cli.cli import cli as root_cli

        from dagster_dg_cli_tests.cli_tests.api_tests.test_dynamic_command_execution import (
            ReplayClient,
        )

        replay_client = ReplayClient(
            [_SAMPLE_LOGS_CAPTURED_RESPONSE, _SAMPLE_CAPTURED_LOGS_RESPONSE]
        )
        test_context = DgApiTestContext(client_factory=lambda config: replay_client)

        runner = CliRunner()
        result = runner.invoke(root_cli, ["api", "run", "get-logs", _RUN_ID], obj=test_context)

        assert "view_graphql" not in (result.output or ""), (
            "Command crashed with view_graphql TypeError"
        )
        assert result.exit_code == 0

    def test_command_step_key_filter(self):
        """--step-key option is accepted."""
        from dagster_dg_cli.cli import cli as root_cli

        from dagster_dg_cli_tests.cli_tests.api_tests.test_dynamic_command_execution import (
            ReplayClient,
        )

        replay_client = ReplayClient(
            [_SAMPLE_LOGS_CAPTURED_RESPONSE, _SAMPLE_CAPTURED_LOGS_RESPONSE]
        )
        test_context = DgApiTestContext(client_factory=lambda config: replay_client)

        runner = CliRunner()
        result = runner.invoke(
            root_cli,
            ["api", "run", "get-logs", _RUN_ID, "--step-key", "my_step"],
            obj=test_context,
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
