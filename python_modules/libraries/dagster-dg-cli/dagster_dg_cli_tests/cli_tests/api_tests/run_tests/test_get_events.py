"""Test run get-events business logic functions and CLI command invocation.

These tests cover the formatting, filtering, and pagination logic for
`dg api run get-events`, consolidated from the former log_tests and run_event_tests.
"""

import json

from click.testing import CliRunner
from dagster_dg_cli.cli.api.client import DgApiTestContext
from dagster_dg_cli.cli.api.formatters import format_logs_json, format_logs_table
from dagster_rest_resources.schemas.enums import DgApiLogLevel
from dagster_rest_resources.schemas.run_event import (
    DgApiErrorInfo,
    DgApiRunEvent,
    DgApiRunEventList,
)


class TestFormatLogs:
    """Test the log formatting functions."""

    def _create_sample_log_list(self):
        """Create sample DgApiRunEventList for testing."""
        events = [
            DgApiRunEvent(
                run_id="test-run-12345",
                message='Starting execution of run for "test_pipeline".',
                timestamp="1641046800000",  # 2022-01-01 14:20:00 UTC (as milliseconds)
                level=DgApiLogLevel.INFO,
                step_key=None,
                event_type="RunStartEvent",
                error=None,
            ),
            DgApiRunEvent(
                run_id="test-run-12345",
                message='Started execution of step "process_data".',
                timestamp="1641046805000",  # 2022-01-01 14:20:05 UTC
                level=DgApiLogLevel.DEBUG,
                step_key="process_data",
                event_type="ExecutionStepStartEvent",
                error=None,
            ),
            DgApiRunEvent(
                run_id="test-run-12345",
                message="Loading input from path: /tmp/input.json",
                timestamp="1641046810000",  # 2022-01-01 14:20:10 UTC
                level=DgApiLogLevel.DEBUG,
                step_key="process_data",
                event_type="MessageEvent",
                error=None,
            ),
            DgApiRunEvent(
                run_id="test-run-12345",
                message='Execution of step "process_data" failed.',
                timestamp="1641046815000",  # 2022-01-01 14:20:15 UTC
                level=DgApiLogLevel.ERROR,
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
                level=DgApiLogLevel.ERROR,
                step_key=None,
                event_type="RunFailureEvent",
                error=None,
            ),
        ]
        return DgApiRunEventList(items=events, cursor=None, has_more=False)

    def _create_empty_log_list(self):
        """Create empty DgApiRunEventList for testing."""
        return DgApiRunEventList(items=[], cursor=None, has_more=False)

    def _create_log_with_nested_error(self):
        """Create log with nested error causes."""
        return DgApiRunEvent(
            run_id="nested-error-run",
            message="Database connection failed with retry exhausted.",
            timestamp="1641046825000",
            level=DgApiLogLevel.ERROR,
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
            level=DgApiLogLevel.INFO,
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
        result = format_logs_json(log_list)

        # For JSON, we want to snapshot the parsed structure to avoid formatting differences
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
        result = format_logs_json(log_list)

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_logs_with_nested_errors(self, snapshot):
        """Test formatting logs with nested error causes."""
        from dagster_shared.utils.timing import fixed_timezone

        log_with_nested_error = self._create_log_with_nested_error()
        log_list = DgApiRunEventList(items=[log_with_nested_error])

        with fixed_timezone("UTC"):
            result = format_logs_table(log_list, "nested-error-run")

        snapshot.assert_match(result)

    def test_format_logs_with_nested_errors_json(self, snapshot):
        """Test formatting logs with nested errors as JSON."""
        log_with_nested_error = self._create_log_with_nested_error()
        log_list = DgApiRunEventList(items=[log_with_nested_error])

        result = format_logs_json(log_list)

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_logs_with_long_step_key(self, snapshot):
        """Test formatting logs with step key truncation."""
        from dagster_shared.utils.timing import fixed_timezone

        log_with_long_key = self._create_log_with_very_long_step_key()
        log_list = DgApiRunEventList(items=[log_with_long_key])

        with fixed_timezone("UTC"):
            result = format_logs_table(log_list, "truncation-test-run")

        snapshot.assert_match(result)

    def test_format_logs_with_pagination_info(self, snapshot):
        """Test formatting logs with pagination indicators."""
        from dagster_shared.utils.timing import fixed_timezone

        # Create log list that has more data available
        log_list = DgApiRunEventList(
            items=[
                DgApiRunEvent(
                    run_id="paginated-run",
                    message="First log entry",
                    timestamp="1641046800000",
                    level=DgApiLogLevel.INFO,
                    step_key=None,
                    event_type="MessageEvent",
                    error=None,
                ),
                DgApiRunEvent(
                    run_id="paginated-run",
                    message="Second log entry",
                    timestamp="1641046805000",
                    level=DgApiLogLevel.DEBUG,
                    step_key="step_1",
                    event_type="MessageEvent",
                    error=None,
                ),
            ],
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
                step_key="test_step" if level != DgApiLogLevel.INFO else None,
                event_type="MessageEvent",
                error=None,
            )
            for level in DgApiLogLevel
        ]

        log_list = DgApiRunEventList(items=events)

        with fixed_timezone("UTC"):
            result = format_logs_table(log_list, "level-test-run")

        snapshot.assert_match(result)


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


_RUN_ID = "a34cd75c-cfa9-4e99-8f0a-955492b89afd"

_SAMPLE_GRAPHQL_RESPONSE = {
    "logsForRun": {
        "__typename": "EventConnection",
        "events": [
            {
                "__typename": "RunStartEvent",
                "runId": _RUN_ID,
                "message": 'Started execution of run for "dbt_analytics_core_job".',
                "timestamp": "1771476078297",
                "level": "INFO",
                "stepKey": None,
                "eventType": "PIPELINE_START",
            },
            {
                "__typename": "AssetMaterializationPlannedEvent",
                "runId": _RUN_ID,
                "message": 'dbt_analytics_core_job intends to materialize asset "my_asset".',
                "timestamp": "1771476078298",
                "level": "INFO",
                "stepKey": "dbt_non_partitioned_models_2",
                "eventType": "ASSET_MATERIALIZATION_PLANNED",
            },
        ],
        "cursor": "",
        "hasMore": False,
    }
}


class TestGetEventsCommandInvocation:
    """Regression tests for `dg api run get-events` CLI invocation."""

    def test_command_accepts_view_graphql_param(self):
        """Regression test: get_events_run_command must accept the view_graphql kwarg.

        The @dg_api_options decorator unconditionally injects view_graphql into kwargs
        (dagster_shared/plus/config_utils.py). If the command function signature is missing
        this parameter, the invocation crashes with:

            TypeError: get_events_run_command() got an unexpected keyword argument 'view_graphql'
        """
        from dagster_dg_cli.cli import cli as root_cli

        from dagster_dg_cli_tests.cli_tests.api_tests.test_dynamic_command_execution import (
            ReplayClient,
        )

        replay_client = ReplayClient([_SAMPLE_GRAPHQL_RESPONSE])
        test_context = DgApiTestContext(client_factory=lambda config: replay_client)

        runner = CliRunner()
        result = runner.invoke(root_cli, ["api", "run", "get-events", _RUN_ID], obj=test_context)

        assert "view_graphql" not in (result.output or ""), (
            "Command crashed with view_graphql TypeError - check get_events_run_command signature"
        )
        assert result.exit_code == 0
