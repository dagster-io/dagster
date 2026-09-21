from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.enums import InstigationStatus, SensorType
from dagster_rest_resources.__generated__.get_sensor import (
    GetSensor,
    GetSensorSensorOrErrorPythonError,
    GetSensorSensorOrErrorSensor,
    GetSensorSensorOrErrorSensorNotFoundError,
    GetSensorSensorOrErrorSensorSensorState,
    GetSensorSensorOrErrorUnauthorizedError,
)
from dagster_rest_resources.__generated__.input_types import RepositorySelector, SensorSelector
from dagster_rest_resources.__generated__.list_repositories_with_sensors import (
    ListRepositoriesWithSensors,
    ListRepositoriesWithSensorsRepositoriesOrErrorPythonError,
    ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnection,
    ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnectionNodes,
    ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnectionNodesLocation,
    ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnectionNodesSensors,
    ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnectionNodesSensorsSensorState,
    ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryNotFoundError,
)
from dagster_rest_resources.__generated__.list_sensors import (
    ListSensors,
    ListSensorsSensorsOrErrorPythonError,
    ListSensorsSensorsOrErrorRepositoryNotFoundError,
    ListSensorsSensorsOrErrorSensors,
    ListSensorsSensorsOrErrorSensorsResults,
    ListSensorsSensorsOrErrorSensorsResultsSensorState,
)
from dagster_rest_resources.api.sensor import DgApiSensorApi
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)
from dagster_rest_resources.schemas.sensor import DgApiSensorList


def _make_sensor_result(
    name: str = "test_sensor_name",
    sensor_id: str = "test-sensor-id",
    status: InstigationStatus = InstigationStatus.RUNNING,
    sensor_type: SensorType = SensorType.STANDARD,
    description: str | None = None,
) -> ListSensorsSensorsOrErrorSensorsResults:
    return ListSensorsSensorsOrErrorSensorsResults(
        id=sensor_id,
        name=name,
        sensorState=ListSensorsSensorsOrErrorSensorsResultsSensorState(
            status=status,
        ),
        sensorType=sensor_type,
        description=description,
    )


def _make_repos(
    sensors: list[tuple[str, str]] | None = None,
) -> ListRepositoriesWithSensors:
    """sensors: list of (sensor_name, sensor_id) tuples."""
    return ListRepositoriesWithSensors(
        repositoriesOrError=ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnection(
            __typename="RepositoryConnection",
            nodes=[
                ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnectionNodes(
                    name="__repository__",
                    location=ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnectionNodesLocation(
                        name="test_location"
                    ),
                    sensors=[
                        ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnectionNodesSensors(
                            id=sid,
                            name=sname,
                            sensorState=ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnectionNodesSensorsSensorState(
                                status=InstigationStatus.RUNNING,
                            ),
                            sensorType=SensorType.STANDARD,
                            description=None,
                        )
                        for sname, sid in (sensors or [])
                    ],
                )
            ],
        )
    )


class TestListSensorsFiltered:
    def test_returns_sensors_for_repo(self):
        client = Mock(spec=IGraphQLClient)
        client.list_sensors.return_value = ListSensors(
            sensorsOrError=ListSensorsSensorsOrErrorSensors(
                __typename="Sensors",
                results=[
                    _make_sensor_result("sensor-a", "id-a"),
                    _make_sensor_result("sensor-b", "id-b"),
                ],
            )
        )

        result = DgApiSensorApi(_client=client).list_sensors(
            repository_location_name="loc",
            repository_name="repo",
        )

        client.list_sensors.assert_called_once_with(
            repository_selector=RepositorySelector(
                repositoryLocationName="loc",
                repositoryName="repo",
            )
        )

        assert result.total == 2
        assert result.items[0].id == "id-a"
        assert result.items[0].repository_origin == "loc@repo"
        assert result.items[1].id == "id-b"
        assert result.items[1].repository_origin == "loc@repo"

    def test_empty_results(self):
        client = Mock(spec=IGraphQLClient)
        client.list_sensors.return_value = ListSensors(
            sensorsOrError=ListSensorsSensorsOrErrorSensors(
                __typename="Sensors",
                results=[],
            )
        )

        result = DgApiSensorApi(_client=client).list_sensors(
            repository_location_name="loc",
            repository_name="repo",
        )

        assert result == DgApiSensorList(items=[])

    def test_repository_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_sensors.return_value = ListSensors(
            sensorsOrError=ListSensorsSensorsOrErrorRepositoryNotFoundError(
                __typename="RepositoryNotFoundError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing sensors"):
            DgApiSensorApi(_client=client).list_sensors(
                repository_location_name="loc",
                repository_name="repo",
            )

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_sensors.return_value = ListSensors(
            sensorsOrError=ListSensorsSensorsOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing sensors"):
            DgApiSensorApi(_client=client).list_sensors(
                repository_location_name="loc",
                repository_name="repo",
            )


class TestListSensorsAll:
    def test_returns_all_sensors_across_repos(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_with_sensors.return_value = _make_repos(
            sensors=[("sensor-a", "id-a"), ("sensor-b", "id-b")]
        )

        result = DgApiSensorApi(_client=client).list_sensors()

        assert result.total == 2
        assert result.items[0].id == "id-a"
        assert result.items[0].repository_origin == "test_location@__repository__"
        assert result.items[1].id == "id-b"
        assert result.items[1].repository_origin == "test_location@__repository__"

    def test_empty_repos(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_with_sensors.return_value = _make_repos(sensors=[])

        result = DgApiSensorApi(_client=client).list_sensors()

        assert result == DgApiSensorList(items=[])

    def test_repo_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_with_sensors.return_value = ListRepositoriesWithSensors(
            repositoriesOrError=ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryNotFoundError(
                __typename="RepositoryNotFoundError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing sensors"):
            DgApiSensorApi(_client=client).list_sensors()

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_with_sensors.return_value = ListRepositoriesWithSensors(
            repositoriesOrError=ListRepositoriesWithSensorsRepositoriesOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing sensors"):
            DgApiSensorApi(_client=client).list_sensors()


class TestGetSensor:
    def test_returns_sensor(self):
        client = Mock(spec=IGraphQLClient)
        client.get_sensor.return_value = GetSensor(
            sensorOrError=GetSensorSensorOrErrorSensor(
                __typename="Sensor",
                id="test-sensor-id",
                name="test-sensor-name",
                sensorState=GetSensorSensorOrErrorSensorSensorState(
                    status=InstigationStatus.RUNNING,
                ),
                sensorType=SensorType.ASSET,
                description="test-sensor-description",
            )
        )

        result = DgApiSensorApi(_client=client).get_sensor(
            sensor_name="test-sensor-name",
            repository_location_name="loc",
            repository_name="repo",
        )

        client.get_sensor.assert_called_once_with(
            sensor_selector=SensorSelector(
                repositoryLocationName="loc",
                repositoryName="repo",
                sensorName="test-sensor-name",
            )
        )

        assert result.id == "test-sensor-id"
        assert result.name == "test-sensor-name"
        assert result.status == InstigationStatus.RUNNING
        assert result.sensor_type == SensorType.ASSET
        assert result.repository_origin == "loc@repo"
        assert result.description == "test-sensor-description"
        assert result.next_tick_timestamp is None

    def test_sensor_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_sensor.return_value = GetSensor(
            sensorOrError=GetSensorSensorOrErrorSensorNotFoundError(
                __typename="SensorNotFoundError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Sensor not found"):
            DgApiSensorApi(_client=client).get_sensor(
                sensor_name="missing",
                repository_location_name="loc",
                repository_name="repo",
            )

    def test_unauthorized_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_sensor.return_value = GetSensor(
            sensorOrError=GetSensorSensorOrErrorUnauthorizedError(
                __typename="UnauthorizedError", message=""
            )
        )

        with pytest.raises(DagsterPlusUnauthorizedError, match="Error fetching sensor"):
            DgApiSensorApi(_client=client).get_sensor(
                sensor_name="test-sensor-name",
                repository_location_name="loc",
                repository_name="repo",
            )

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_sensor.return_value = GetSensor(
            sensorOrError=GetSensorSensorOrErrorPythonError(__typename="PythonError", message="")
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching sensor"):
            DgApiSensorApi(_client=client).get_sensor(
                sensor_name="test-sensor-name",
                repository_location_name="loc",
                repository_name="repo",
            )


class TestGetSensorByName:
    def test_finds_sensor_by_name(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_with_sensors.return_value = _make_repos(
            sensors=[("target_sensor", "id-target"), ("other_sensor", "id-other")]
        )

        result = DgApiSensorApi(_client=client).get_sensor_by_name("target_sensor")

        assert result.id == "id-target"
        assert result.repository_origin == "test_location@__repository__"

    def test_sensor_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_with_sensors.return_value = _make_repos(
            sensors=[("other_sensor", "id-other")]
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Sensor not found: missing_sensor"):
            DgApiSensorApi(_client=client).get_sensor_by_name("missing_sensor")

    def test_multiple_matching_sensors_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_with_sensors.return_value = ListRepositoriesWithSensors(
            repositoriesOrError=ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnection(
                __typename="RepositoryConnection",
                nodes=[
                    ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnectionNodes(
                        name="repo_a",
                        location=ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnectionNodesLocation(
                            name="loc_a"
                        ),
                        sensors=[
                            ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnectionNodesSensors(
                                id="id_1",
                                name="dup_sensor",
                                sensorState=ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnectionNodesSensorsSensorState(
                                    status=InstigationStatus.RUNNING,
                                ),
                                sensorType=SensorType.STANDARD,
                                description=None,
                            )
                        ],
                    ),
                    ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnectionNodes(
                        name="repo_b",
                        location=ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnectionNodesLocation(
                            name="loc_b"
                        ),
                        sensors=[
                            ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnectionNodesSensors(
                                id="id_2",
                                name="dup_sensor",
                                sensorState=ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnectionNodesSensorsSensorState(
                                    status=InstigationStatus.STOPPED,
                                ),
                                sensorType=SensorType.STANDARD,
                                description=None,
                            )
                        ],
                    ),
                ],
            )
        )

        with pytest.raises(
            DagsterPlusGraphqlError,
            match="Multiple sensors found with name 'dup_sensor' in repositories: loc_a@repo_a, loc_b@repo_b",
        ):
            DgApiSensorApi(_client=client).get_sensor_by_name("dup_sensor")

    def test_repo_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_with_sensors.return_value = ListRepositoriesWithSensors(
            repositoriesOrError=ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryNotFoundError(
                __typename="RepositoryNotFoundError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing repositories"):
            DgApiSensorApi(_client=client).get_sensor_by_name("test_sensor_name")

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_with_sensors.return_value = ListRepositoriesWithSensors(
            repositoriesOrError=ListRepositoriesWithSensorsRepositoriesOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing repositories"):
            DgApiSensorApi(_client=client).get_sensor_by_name("test_sensor_name")
