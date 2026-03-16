"""Test get-ticks business logic and CLI command invocation.

Covers the tick adapter, formatting, and CLI invocation for both
`dg api sensor get-ticks` and `dg api schedule get-ticks`.
"""

import json
from unittest.mock import MagicMock

from click.testing import CliRunner
from dagster_dg_cli.api_layer.graphql_adapter.tick import (
    _find_selector_for_name,
    _process_ticks_response,
    get_schedule_ticks_via_graphql,
    get_sensor_ticks_via_graphql,
)
from dagster_dg_cli.api_layer.schemas.tick import (
    DgApiTick,
    DgApiTickError,
    DgApiTickList,
    DgApiTickStatus,
)
from dagster_dg_cli.cli.api.client import DgApiTestContext
from dagster_dg_cli.cli.api.formatters import format_ticks

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
# Adapter tests
# ---------------------------------------------------------------------------


class TestFindSelectorForName:
    def test_finds_sensor(self):
        client = MagicMock()
        client.execute.return_value = _REPOS_RESPONSE

        selector = _find_selector_for_name(client, "my_sensor", "sensor")
        assert selector["sensorName"] == "my_sensor"
        assert selector["repositoryLocationName"] == "my_location"
        assert selector["repositoryName"] == "__repository__"

    def test_finds_schedule(self):
        client = MagicMock()
        client.execute.return_value = _REPOS_RESPONSE

        selector = _find_selector_for_name(client, "my_schedule", "schedule")
        assert selector["scheduleName"] == "my_schedule"

    def test_not_found_raises(self):
        client = MagicMock()
        client.execute.return_value = _REPOS_RESPONSE

        try:
            _find_selector_for_name(client, "nonexistent", "sensor")
            assert False, "Should have raised"
        except Exception as e:
            assert "not found" in str(e).lower()

    def test_multiple_matches_raises(self):
        client = MagicMock()
        client.execute.return_value = {
            "repositoriesOrError": {
                "__typename": "RepositoryConnection",
                "nodes": [
                    {
                        "name": "repo1",
                        "location": {"name": "loc1"},
                        "sensors": [{"name": "dup_sensor"}],
                        "schedules": [],
                    },
                    {
                        "name": "repo2",
                        "location": {"name": "loc2"},
                        "sensors": [{"name": "dup_sensor"}],
                        "schedules": [],
                    },
                ],
            }
        }

        try:
            _find_selector_for_name(client, "dup_sensor", "sensor")
            assert False, "Should have raised"
        except Exception as e:
            assert "Multiple" in str(e)


class TestProcessTicksResponse:
    def test_processes_ticks(self):
        result = _process_ticks_response(_SAMPLE_TICKS)
        assert len(result.items) == 3
        assert result.items[0].status == DgApiTickStatus.SUCCESS
        assert result.items[0].run_ids == ["run-abc"]
        assert result.items[1].status == DgApiTickStatus.SKIPPED
        assert result.items[1].skip_reason == "No new data"
        assert result.items[2].status == DgApiTickStatus.FAILURE
        assert result.items[2].error is not None
        assert "timeout" in result.items[2].error.message

    def test_empty_ticks(self):
        result = _process_ticks_response([])
        assert result.items == []
        assert result.total == 0
        assert result.cursor is None

    def test_cursor_from_last_tick(self):
        result = _process_ticks_response(_SAMPLE_TICKS)
        assert result.cursor == "tick-3"


class TestGetSensorTicksViaGraphql:
    def test_basic_fetch(self):
        client = MagicMock()
        client.execute.side_effect = [
            _REPOS_RESPONSE,
            _make_sensor_ticks_response(_SAMPLE_TICKS),
        ]

        result = get_sensor_ticks_via_graphql(client, sensor_name="my_sensor")
        assert len(result.items) == 3
        assert client.execute.call_count == 2

    def test_passes_filter_variables(self):
        client = MagicMock()
        client.execute.side_effect = [
            _REPOS_RESPONSE,
            _make_sensor_ticks_response([]),
        ]

        get_sensor_ticks_via_graphql(
            client,
            sensor_name="my_sensor",
            limit=10,
            statuses=("SUCCESS",),
            before_timestamp=1700000000.0,
        )

        # Second call is the ticks query
        call_args = client.execute.call_args_list[1]
        variables = call_args[0][1]
        assert variables["limit"] == 10
        assert variables["statuses"] == ["SUCCESS"]
        assert variables["beforeTimestamp"] == 1700000000.0

    def test_sensor_not_found(self):
        client = MagicMock()
        client.execute.side_effect = [
            _REPOS_RESPONSE,
            {
                "sensorOrError": {
                    "__typename": "SensorNotFoundError",
                    "message": "Sensor not found",
                }
            },
        ]

        try:
            get_sensor_ticks_via_graphql(client, sensor_name="my_sensor")
            assert False, "Should have raised"
        except Exception as e:
            assert "not found" in str(e).lower()


class TestGetScheduleTicksViaGraphql:
    def test_basic_fetch(self):
        client = MagicMock()
        client.execute.side_effect = [
            _REPOS_RESPONSE,
            _make_schedule_ticks_response(_SAMPLE_TICKS),
        ]

        result = get_schedule_ticks_via_graphql(client, schedule_name="my_schedule")
        assert len(result.items) == 3


# ---------------------------------------------------------------------------
# Formatter tests
# ---------------------------------------------------------------------------


class TestFormatTicks:
    def _create_sample_tick_list(self):
        return DgApiTickList(
            items=[
                DgApiTick(
                    id="tick-1",
                    status=DgApiTickStatus.SUCCESS,
                    timestamp=1641046800.0,
                    end_timestamp=1641046810.0,
                    run_ids=["run-abc"],
                    error=None,
                    skip_reason=None,
                    cursor=None,
                ),
                DgApiTick(
                    id="tick-2",
                    status=DgApiTickStatus.SKIPPED,
                    timestamp=1641046700.0,
                    end_timestamp=None,
                    run_ids=[],
                    error=None,
                    skip_reason="No new data",
                    cursor=None,
                ),
                DgApiTick(
                    id="tick-3",
                    status=DgApiTickStatus.FAILURE,
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
