"""Test get-ticks business logic and CLI command invocation.

Covers the tick adapter, formatting, and CLI invocation for both
`dg api sensor get-ticks` and `dg api schedule get-ticks`.
"""

import json

from click.testing import CliRunner
from dagster_dg_cli.cli.api.client import DgApiTestContext
from dagster_dg_cli.cli.api.formatters import format_ticks
from dagster_rest_resources.schemas.enums import DgApiInstigationTickStatus
from dagster_rest_resources.schemas.tick import DgApiTick, DgApiTickError, DgApiTickList

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

_REPOS_RESPONSE = {
    "repositoriesOrError": {
        "__typename": "RepositoryConnection",
        "nodes": [
            {
                "name": "__repository__",
                "location": {"name": "my_location"},
                "sensors": [{"name": "my_sensor"}],
                "schedules": [{"name": "my_schedule"}],
            },
        ],
    }
}

_SAMPLE_TICKS = [
    {
        "id": "tick-1",
        "status": "SUCCESS",
        "timestamp": 1641046800.0,
        "endTimestamp": 1641046810.0,
        "runIds": ["run-abc"],
        "skipReason": None,
        "cursor": None,
        "error": None,
    },
    {
        "id": "tick-2",
        "status": "SKIPPED",
        "timestamp": 1641046700.0,
        "endTimestamp": 1641046700.5,
        "runIds": [],
        "skipReason": "No new data",
        "cursor": None,
        "error": None,
    },
    {
        "id": "tick-3",
        "status": "FAILURE",
        "timestamp": 1641046600.0,
        "endTimestamp": 1641046605.0,
        "runIds": [],
        "skipReason": None,
        "cursor": None,
        "error": {
            "message": "ConnectionError: timeout\n",
            "stack": [
                '  File "/app/sensor.py", line 10, in evaluate\n    data = fetch()\n',
            ],
        },
    },
]


def _make_sensor_ticks_response(ticks):
    return {
        "sensorOrError": {
            "__typename": "Sensor",
            "name": "my_sensor",
            "sensorState": {"ticks": ticks},
        }
    }


def _make_schedule_ticks_response(ticks):
    return {
        "scheduleOrError": {
            "__typename": "Schedule",
            "name": "my_schedule",
            "scheduleState": {"ticks": ticks},
        }
    }


# ---------------------------------------------------------------------------
# Formatter tests
# ---------------------------------------------------------------------------


class TestFormatTicks:
    def _create_sample_tick_list(self):
        return DgApiTickList(
            items=[
                DgApiTick(
                    id="tick-1",
                    status=DgApiInstigationTickStatus.SUCCESS,
                    timestamp=1641046800.0,
                    end_timestamp=1641046810.0,
                    run_ids=["run-abc"],
                    error=None,
                    skip_reason=None,
                    cursor=None,
                ),
                DgApiTick(
                    id="tick-2",
                    status=DgApiInstigationTickStatus.SKIPPED,
                    timestamp=1641046700.0,
                    end_timestamp=None,
                    run_ids=[],
                    error=None,
                    skip_reason="No new data",
                    cursor=None,
                ),
                DgApiTick(
                    id="tick-3",
                    status=DgApiInstigationTickStatus.FAILURE,
                    timestamp=1641046600.0,
                    end_timestamp=None,
                    run_ids=[],
                    error=DgApiTickError(
                        message="ConnectionError: timeout",
                        stack=['  File "/app/sensor.py", line 10\n'],
                    ),
                    skip_reason=None,
                    cursor=None,
                ),
            ],
            total=3,
            cursor="tick-3",
        )

    def test_format_ticks_table(self, snapshot):
        from dagster_shared.utils.timing import fixed_timezone

        ticks = self._create_sample_tick_list()
        with fixed_timezone("UTC"):
            result = format_ticks(ticks, name="my_sensor", as_json=False)
        snapshot.assert_match(result)

    def test_format_ticks_json(self, snapshot):
        ticks = self._create_sample_tick_list()
        result = format_ticks(ticks, name="my_sensor", as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_empty_ticks(self):
        ticks = DgApiTickList(items=[], total=0, cursor=None)
        result = format_ticks(ticks, name="my_sensor", as_json=False)
        assert "No ticks found for my_sensor" in result


# ---------------------------------------------------------------------------
# CLI invocation tests
# ---------------------------------------------------------------------------


class TestGetSensorTicksCommandInvocation:
    def test_basic_invocation(self):
        from dagster_dg_cli.cli import cli as root_cli

        from dagster_dg_cli_tests.cli_tests.api_tests.test_dynamic_command_execution import (
            ReplayClient,
        )

        replay_client = ReplayClient([_REPOS_RESPONSE, _make_sensor_ticks_response(_SAMPLE_TICKS)])
        test_context = DgApiTestContext(client_factory=lambda config: replay_client)

        runner = CliRunner()
        result = runner.invoke(
            root_cli, ["api", "sensor", "get-ticks", "my_sensor"], obj=test_context
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "SUCCESS" in result.output

    def test_json_output(self):
        from dagster_dg_cli.cli import cli as root_cli

        from dagster_dg_cli_tests.cli_tests.api_tests.test_dynamic_command_execution import (
            ReplayClient,
        )

        replay_client = ReplayClient([_REPOS_RESPONSE, _make_sensor_ticks_response(_SAMPLE_TICKS)])
        test_context = DgApiTestContext(client_factory=lambda config: replay_client)

        runner = CliRunner()
        result = runner.invoke(
            root_cli, ["api", "sensor", "get-ticks", "my_sensor", "--json"], obj=test_context
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        parsed = json.loads(result.output)
        assert len(parsed["items"]) == 3

    def test_accepts_view_graphql_param(self):
        from dagster_dg_cli.cli import cli as root_cli

        from dagster_dg_cli_tests.cli_tests.api_tests.test_dynamic_command_execution import (
            ReplayClient,
        )

        replay_client = ReplayClient([_REPOS_RESPONSE, _make_sensor_ticks_response(_SAMPLE_TICKS)])
        test_context = DgApiTestContext(client_factory=lambda config: replay_client)

        runner = CliRunner()
        result = runner.invoke(
            root_cli, ["api", "sensor", "get-ticks", "my_sensor"], obj=test_context
        )

        assert "view_graphql" not in (result.output or "")
        assert result.exit_code == 0


class TestGetScheduleTicksCommandInvocation:
    def test_basic_invocation(self):
        from dagster_dg_cli.cli import cli as root_cli

        from dagster_dg_cli_tests.cli_tests.api_tests.test_dynamic_command_execution import (
            ReplayClient,
        )

        replay_client = ReplayClient(
            [_REPOS_RESPONSE, _make_schedule_ticks_response(_SAMPLE_TICKS)]
        )
        test_context = DgApiTestContext(client_factory=lambda config: replay_client)

        runner = CliRunner()
        result = runner.invoke(
            root_cli, ["api", "schedule", "get-ticks", "my_schedule"], obj=test_context
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "SUCCESS" in result.output

    def test_json_output(self):
        from dagster_dg_cli.cli import cli as root_cli

        from dagster_dg_cli_tests.cli_tests.api_tests.test_dynamic_command_execution import (
            ReplayClient,
        )

        replay_client = ReplayClient(
            [_REPOS_RESPONSE, _make_schedule_ticks_response(_SAMPLE_TICKS)]
        )
        test_context = DgApiTestContext(client_factory=lambda config: replay_client)

        runner = CliRunner()
        result = runner.invoke(
            root_cli, ["api", "schedule", "get-ticks", "my_schedule", "--json"], obj=test_context
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        parsed = json.loads(result.output)
        assert len(parsed["items"]) == 3
