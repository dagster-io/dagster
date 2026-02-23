"""Test run event business logic functions and CLI command invocation.

Includes a regression test for:
    TypeError: get_run_events_command() got an unexpected keyword argument 'view_graphql'
"""

import json

from click.testing import CliRunner
from dagster_dg_cli.api_layer.schemas.run_event import DgApiRunEvent, RunEventLevel, RunEventList
from dagster_dg_cli.cli.api.client import DgApiTestContext
from dagster_dg_cli.cli.api.run_event import format_run_events_json, format_run_events_table

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


def _make_sample_events() -> RunEventList:
    return RunEventList(
        items=[
            DgApiRunEvent(
                run_id=_RUN_ID,
                message='Started execution of run for "dbt_analytics_core_job".',
                timestamp="1771476078297",
                level=RunEventLevel.INFO,
                step_key=None,
                event_type="PIPELINE_START",
            ),
            DgApiRunEvent(
                run_id=_RUN_ID,
                message='dbt_analytics_core_job intends to materialize asset "my_asset".',
                timestamp="1771476078298",
                level=RunEventLevel.INFO,
                step_key="dbt_non_partitioned_models_2",
                event_type="ASSET_MATERIALIZATION_PLANNED",
            ),
        ],
        total=2,
    )


class TestFormatRunEventsTable:
    def test_format_with_events(self, snapshot):
        events = _make_sample_events()
        result = format_run_events_table(events, _RUN_ID)
        snapshot.assert_match(result)

    def test_format_empty_events(self):
        events = RunEventList(items=[], total=0)
        result = format_run_events_table(events, _RUN_ID)
        assert result == f"No events found for run {_RUN_ID}"


class TestFormatRunEventsJson:
    def test_format_with_events(self, snapshot):
        events = _make_sample_events()
        result = format_run_events_json(events, _RUN_ID)
        snapshot.assert_match(json.loads(result))

    def test_format_empty_events(self):
        events = RunEventList(items=[], total=0)
        result = format_run_events_json(events, _RUN_ID)
        parsed = json.loads(result)
        assert parsed["run_id"] == _RUN_ID
        assert parsed["events"] == []
        assert parsed["count"] == 0


class TestGetRunEventsCommandInvocation:
    """Regression tests for `dg api run-events get` CLI invocation."""

    def test_command_accepts_view_graphql_param(self):
        """Regression test: get_run_events_command must accept the view_graphql kwarg.

        The @dg_api_options decorator unconditionally injects view_graphql into kwargs
        (dagster_shared/plus/config_utils.py). If the command function signature is missing
        this parameter, the invocation crashes with:

            TypeError: get_run_events_command() got an unexpected keyword argument 'view_graphql'
        """
        from dagster_dg_cli.cli import cli as root_cli

        from dagster_dg_cli_tests.cli_tests.api_tests.test_dynamic_command_execution import (
            ReplayClient,
        )

        replay_client = ReplayClient([_SAMPLE_GRAPHQL_RESPONSE])
        test_context = DgApiTestContext(client_factory=lambda config: replay_client)

        runner = CliRunner()
        result = runner.invoke(root_cli, ["api", "run-events", "get", _RUN_ID], obj=test_context)

        assert "view_graphql" not in (result.output or ""), (
            "Command crashed with view_graphql TypeError - check get_run_events_command signature"
        )
        assert result.exit_code == 0
