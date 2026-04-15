"""Test run get-logs business logic functions and CLI command invocation.

These tests cover the adapter, formatting, and CLI logic for
`dg api run get-logs`.
"""

import json

from click.testing import CliRunner
from dagster_dg_cli.cli.api.client import DgApiTestContext
from dagster_dg_cli.cli.api.formatters import format_compute_log_links, format_compute_logs
from dagster_rest_resources.schemas.compute_log import (
    DgApiComputeLogLinkList,
    DgApiComputeLogList,
    DgApiStepComputeLog,
    DgApiStepComputeLogLink,
)

_RUN_ID = "b45fff8a-7def-43b8-805d-1cf5f435c997"


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
