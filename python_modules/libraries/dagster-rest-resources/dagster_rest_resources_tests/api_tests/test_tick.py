from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.enums import InstigationTickStatus
from dagster_rest_resources.__generated__.get_schedule_ticks import (
    GetScheduleTicks,
    GetScheduleTicksScheduleOrErrorPythonError,
    GetScheduleTicksScheduleOrErrorSchedule,
    GetScheduleTicksScheduleOrErrorScheduleNotFoundError,
    GetScheduleTicksScheduleOrErrorScheduleScheduleState,
    GetScheduleTicksScheduleOrErrorScheduleScheduleStateTicks,
)
from dagster_rest_resources.__generated__.get_sensor_ticks import (
    GetSensorTicks,
    GetSensorTicksSensorOrErrorPythonError,
    GetSensorTicksSensorOrErrorSensor,
    GetSensorTicksSensorOrErrorSensorNotFoundError,
    GetSensorTicksSensorOrErrorSensorSensorState,
    GetSensorTicksSensorOrErrorSensorSensorStateTicks,
    GetSensorTicksSensorOrErrorSensorSensorStateTicksError,
    GetSensorTicksSensorOrErrorUnauthorizedError,
)
from dagster_rest_resources.__generated__.input_types import ScheduleSelector, SensorSelector
from dagster_rest_resources.__generated__.list_repositories_for_ticks import (
    ListRepositoriesForTicks,
    ListRepositoriesForTicksRepositoriesOrErrorPythonError,
    ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnection,
    ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodes,
    ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodesLocation,
    ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodesSchedules,
    ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodesSensors,
    ListRepositoriesForTicksRepositoriesOrErrorRepositoryNotFoundError,
)
from dagster_rest_resources.api.tick import DgApiTickApi
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)
from dagster_rest_resources.schemas.tick import DgApiTickList


def _make_repos(sensors: list[str] | None = None, schedules: list[str] | None = None):
    return ListRepositoriesForTicks(
        repositoriesOrError=ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnection(
            __typename="RepositoryConnection",
            nodes=[
                ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodes(
                    name="__repository__",
                    location=ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodesLocation(
                        name="test_name"
                    ),
                    sensors=[
                        ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodesSensors(
                            name=s
                        )
                        for s in sensors or []
                    ],
                    schedules=[
                        ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodesSchedules(
                            name=s
                        )
                        for s in schedules or []
                    ],
                )
            ],
        )
    )


def _make_sensor_ticks_result(ticks):
    return GetSensorTicks(
        sensorOrError=GetSensorTicksSensorOrErrorSensor(
            __typename="Sensor",
            name="test_name",
            sensorState=GetSensorTicksSensorOrErrorSensorSensorState(ticks=ticks),
        )
    )


def _make_schedule_ticks_result(ticks):
    return GetScheduleTicks(
        scheduleOrError=GetScheduleTicksScheduleOrErrorSchedule(
            __typename="Schedule",
            name="test_name",
            scheduleState=GetScheduleTicksScheduleOrErrorScheduleScheduleState(ticks=ticks),
        )
    )


_SAMPLE_SENSOR_TICKS = [
    GetSensorTicksSensorOrErrorSensorSensorStateTicks(
        id="tick-1",
        status=InstigationTickStatus.SUCCESS,
        timestamp=1641046800.0,
        endTimestamp=1641046810.0,
        runIds=["run-abc"],
        skipReason=None,
        cursor=None,
        error=None,
    ),
    GetSensorTicksSensorOrErrorSensorSensorStateTicks(
        id="tick-2",
        status=InstigationTickStatus.SKIPPED,
        timestamp=1641046700.0,
        endTimestamp=None,
        runIds=[],
        skipReason="No new data",
        cursor=None,
        error=None,
    ),
    GetSensorTicksSensorOrErrorSensorSensorStateTicks(
        id="tick-3",
        status=InstigationTickStatus.FAILURE,
        timestamp=1641046600.0,
        endTimestamp=None,
        runIds=[],
        skipReason=None,
        cursor=None,
        error=GetSensorTicksSensorOrErrorSensorSensorStateTicksError(
            message="ConnectionError: timeout",
            stack=['  File "/app/sensor.py", line 10\n'],
        ),
    ),
]

_SAMPLE_SCHEDULE_TICKS = [
    GetScheduleTicksScheduleOrErrorScheduleScheduleStateTicks(
        id="tick-1",
        status=InstigationTickStatus.SUCCESS,
        timestamp=1641046800.0,
        endTimestamp=1641046810.0,
        runIds=["run-abc"],
        skipReason=None,
        cursor=None,
        error=None,
    ),
]


class TestGetSensorTicks:
    def test_returns_ticks(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_for_ticks.return_value = _make_repos(sensors=["test_sensor"])
        client.get_sensor_ticks.return_value = _make_sensor_ticks_result(_SAMPLE_SENSOR_TICKS)

        result = DgApiTickApi(_client=client).get_sensor_ticks(sensor_name="test_sensor")

        client.get_sensor_ticks.assert_called_once_with(
            sensor_selector=SensorSelector(
                repositoryLocationName="test_name",
                repositoryName="__repository__",
                sensorName="test_sensor",
            ),
            limit=25,
            cursor=None,
            statuses=None,
            before_timestamp=None,
            after_timestamp=None,
        )

        assert len(result.items) == 3
        assert result.total == 3
        assert result.items[0].status == InstigationTickStatus.SUCCESS
        assert result.items[0].run_ids == ["run-abc"]
        assert result.items[1].status == InstigationTickStatus.SKIPPED
        assert result.items[1].skip_reason == "No new data"
        assert result.items[2].status == InstigationTickStatus.FAILURE
        assert result.items[2].error is not None
        assert "timeout" in result.items[2].error.message

        assert result.cursor == "tick-3"

    def test_empty_ticks(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_for_ticks.return_value = _make_repos(sensors=["test_sensor"])
        client.get_sensor_ticks.return_value = _make_sensor_ticks_result([])

        result = DgApiTickApi(_client=client).get_sensor_ticks(sensor_name="test_sensor")

        assert result == DgApiTickList(items=[], total=0, cursor=None)

    def test_sensor_not_found_in_repo_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_for_ticks.return_value = _make_repos(sensors=[])

        with pytest.raises(DagsterPlusGraphqlError, match="Sensor not found: nonexistent"):
            DgApiTickApi(_client=client).get_sensor_ticks(sensor_name="nonexistent")

    def test_multiple_matching_sensor_found_in_repo_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_for_ticks.return_value = ListRepositoriesForTicks(
            repositoriesOrError=ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnection(
                __typename="RepositoryConnection",
                nodes=[
                    ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodes(
                        name="repo_a",
                        location=ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodesLocation(
                            name="loc_a"
                        ),
                        sensors=[
                            ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodesSensors(
                                name="dup_sensor"
                            )
                        ],
                        schedules=[],
                    ),
                    ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodes(
                        name="repo_b",
                        location=ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodesLocation(
                            name="loc_b"
                        ),
                        sensors=[
                            ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodesSensors(
                                name="dup_sensor"
                            )
                        ],
                        schedules=[],
                    ),
                ],
            )
        )

        with pytest.raises(
            DagsterPlusGraphqlError,
            match="Multiple sensors with name 'dup_sensor': loc_a@repo_a, loc_b@repo_b",
        ):
            DgApiTickApi(_client=client).get_sensor_ticks(sensor_name="dup_sensor")

    def test_repo_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_for_ticks.return_value = ListRepositoriesForTicks(
            repositoriesOrError=ListRepositoriesForTicksRepositoriesOrErrorRepositoryNotFoundError(
                __typename="RepositoryNotFoundError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing repositories"):
            DgApiTickApi(_client=client).get_sensor_ticks(sensor_name="test_sensor")

    def test_python_error_from_repo_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_for_ticks.return_value = ListRepositoriesForTicks(
            repositoriesOrError=ListRepositoriesForTicksRepositoriesOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing repositories"):
            DgApiTickApi(_client=client).get_sensor_ticks(sensor_name="test_sensor")

    def test_sensor_not_found_error_from_sensor_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_for_ticks.return_value = _make_repos(sensors=["test_sensor"])
        client.get_sensor_ticks.return_value = GetSensorTicks(
            sensorOrError=GetSensorTicksSensorOrErrorSensorNotFoundError(
                __typename="SensorNotFoundError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Sensor not found"):
            DgApiTickApi(_client=client).get_sensor_ticks(sensor_name="test_sensor")

    def test_unauthorized_error_from_sensor_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_for_ticks.return_value = _make_repos(sensors=["test_sensor"])
        client.get_sensor_ticks.return_value = GetSensorTicks(
            sensorOrError=GetSensorTicksSensorOrErrorUnauthorizedError(
                __typename="UnauthorizedError", message=""
            )
        )

        with pytest.raises(DagsterPlusUnauthorizedError, match="Error fetching sensor ticks"):
            DgApiTickApi(_client=client).get_sensor_ticks(sensor_name="test_sensor")

    def test_python_error_from_sensor_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_for_ticks.return_value = _make_repos(sensors=["test_sensor"])
        client.get_sensor_ticks.return_value = GetSensorTicks(
            sensorOrError=GetSensorTicksSensorOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching sensor ticks"):
            DgApiTickApi(_client=client).get_sensor_ticks(sensor_name="test_sensor")


class TestGetScheduleTicks:
    def test_returns_ticks(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_for_ticks.return_value = _make_repos(schedules=["test_schedule"])
        client.get_schedule_ticks.return_value = _make_schedule_ticks_result(_SAMPLE_SCHEDULE_TICKS)

        result = DgApiTickApi(_client=client).get_schedule_ticks(schedule_name="test_schedule")

        client.get_schedule_ticks.assert_called_once_with(
            schedule_selector=ScheduleSelector(
                repositoryLocationName="test_name",
                repositoryName="__repository__",
                scheduleName="test_schedule",
            ),
            limit=25,
            cursor=None,
            statuses=None,
            before_timestamp=None,
            after_timestamp=None,
        )

        assert len(result.items) == 1
        assert result.items[0].id == "tick-1"

    def test_empty_ticks(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_for_ticks.return_value = _make_repos(schedules=["test_schedule"])
        client.get_schedule_ticks.return_value = _make_schedule_ticks_result([])

        result = DgApiTickApi(_client=client).get_schedule_ticks(schedule_name="test_schedule")

        assert result == DgApiTickList(items=[], total=0, cursor=None)

    def test_schedule_not_found_in_repo_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_for_ticks.return_value = _make_repos(schedules=[])

        with pytest.raises(DagsterPlusGraphqlError, match="Schedule not found"):
            DgApiTickApi(_client=client).get_schedule_ticks(schedule_name="nonexistent")

    def test_multiple_matching_schedule_found_in_repo_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_for_ticks.return_value = ListRepositoriesForTicks(
            repositoriesOrError=ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnection(
                __typename="RepositoryConnection",
                nodes=[
                    ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodes(
                        name="repo_a",
                        location=ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodesLocation(
                            name="loc_a"
                        ),
                        sensors=[],
                        schedules=[
                            ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodesSchedules(
                                name="dup_schedule"
                            )
                        ],
                    ),
                    ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodes(
                        name="repo_b",
                        location=ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodesLocation(
                            name="loc_b"
                        ),
                        sensors=[],
                        schedules=[
                            ListRepositoriesForTicksRepositoriesOrErrorRepositoryConnectionNodesSchedules(
                                name="dup_schedule"
                            )
                        ],
                    ),
                ],
            )
        )

        with pytest.raises(
            DagsterPlusGraphqlError,
            match="Multiple schedules with name 'dup_schedule': loc_a@repo_a, loc_b@repo_b",
        ):
            DgApiTickApi(_client=client).get_schedule_ticks(schedule_name="dup_schedule")

    def test_repo_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_for_ticks.return_value = ListRepositoriesForTicks(
            repositoriesOrError=ListRepositoriesForTicksRepositoriesOrErrorRepositoryNotFoundError(
                __typename="RepositoryNotFoundError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing repositories"):
            DgApiTickApi(_client=client).get_schedule_ticks(schedule_name="test_schedule")

    def test_python_error_from_repo_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_for_ticks.return_value = ListRepositoriesForTicks(
            repositoriesOrError=ListRepositoriesForTicksRepositoriesOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing repositories"):
            DgApiTickApi(_client=client).get_schedule_ticks(schedule_name="test_schedule")

    def test_schedule_not_found_error_from_schedule_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_for_ticks.return_value = _make_repos(schedules=["test_schedule"])
        client.get_schedule_ticks.return_value = GetScheduleTicks(
            scheduleOrError=GetScheduleTicksScheduleOrErrorScheduleNotFoundError(
                __typename="ScheduleNotFoundError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching schedule ticks"):
            DgApiTickApi(_client=client).get_schedule_ticks(schedule_name="test_schedule")

    def test_python_error_from_schedule_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_for_ticks.return_value = _make_repos(schedules=["test_schedule"])
        client.get_schedule_ticks.return_value = GetScheduleTicks(
            scheduleOrError=GetScheduleTicksScheduleOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching schedule ticks"):
            DgApiTickApi(_client=client).get_schedule_ticks(schedule_name="test_schedule")
