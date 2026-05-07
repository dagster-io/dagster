from dataclasses import dataclass
from typing import TYPE_CHECKING

from typing_extensions import assert_never

from dagster_rest_resources.__generated__.input_types import RepositorySelector, SensorSelector
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)
from dagster_rest_resources.schemas.sensor import DgApiSensor, DgApiSensorList

if TYPE_CHECKING:
    from dagster_rest_resources.__generated__.get_sensor import GetSensorSensorOrErrorSensor
    from dagster_rest_resources.__generated__.list_repositories_with_sensors import (
        ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnectionNodesSensors,
    )
    from dagster_rest_resources.__generated__.list_sensors import (
        ListSensorsSensorsOrErrorSensorsResults,
    )


@dataclass(frozen=True)
class DgApiSensorApi:
    _client: IGraphQLClient

    def list_sensors(
        self,
        repository_location_name: str | None = None,
        repository_name: str | None = None,
    ) -> DgApiSensorList:
        if repository_location_name and repository_name:
            result = self._client.list_sensors(
                repository_selector=RepositorySelector(
                    repositoryLocationName=repository_location_name,
                    repositoryName=repository_name,
                )
            ).sensors_or_error

            match result.typename__:
                case "Sensors":
                    items = [
                        self._build_sensor(
                            s,
                            repo_location_name=repository_location_name,
                            repo_name=repository_name,
                        )
                        for s in result.results  # ty: ignore[unresolved-attribute]
                    ]
                    return DgApiSensorList(items=items)
                case "RepositoryNotFoundError":
                    raise DagsterPlusGraphqlError(f"Error listing sensors: {result.message}")  # ty: ignore[unresolved-attribute]
                case "PythonError":
                    raise DagsterPlusGraphqlError(f"Error listing sensors: {result.message}")  # ty: ignore[unresolved-attribute]
                case _ as unreachable:
                    assert_never(unreachable)
        else:
            result = self._client.list_repositories_with_sensors().repositories_or_error

            match result.typename__:
                case "RepositoryConnection":
                    items = []
                    for repo in result.nodes:  # ty: ignore[unresolved-attribute]
                        for s in repo.sensors:
                            items.append(
                                self._build_sensor(
                                    s,
                                    repo_location_name=repo.location.name,
                                    repo_name=repo.name,
                                )
                            )
                    return DgApiSensorList(items=items)
                case "RepositoryNotFoundError":
                    raise DagsterPlusGraphqlError(f"Error listing sensors: {result.message}")  # ty: ignore[unresolved-attribute]
                case "PythonError":
                    raise DagsterPlusGraphqlError(f"Error listing sensors: {result.message}")  # ty: ignore[unresolved-attribute]
                case _ as unreachable:
                    assert_never(unreachable)

    def get_sensor(
        self,
        sensor_name: str,
        repository_location_name: str,
        repository_name: str,
    ) -> DgApiSensor:
        result = self._client.get_sensor(
            sensor_selector=SensorSelector(
                repositoryLocationName=repository_location_name,
                repositoryName=repository_name,
                sensorName=sensor_name,
            )
        ).sensor_or_error

        match result.typename__:
            case "Sensor":
                return self._build_sensor(
                    result,  # ty: ignore[invalid-argument-type]
                    repo_location_name=repository_location_name,
                    repo_name=repository_name,
                )
            case "SensorNotFoundError":
                raise DagsterPlusGraphqlError(f"Sensor not found: {result.message}")  # ty: ignore[unresolved-attribute]
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(f"Error fetching sensor: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error fetching sensor: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def get_sensor_by_name(self, sensor_name: str) -> DgApiSensor:
        result = self._client.list_repositories_with_sensors().repositories_or_error

        match result.typename__:
            case "RepositoryConnection":
                matches: list[DgApiSensor] = []
                for repo in result.nodes:  # ty: ignore[unresolved-attribute]
                    for s in repo.sensors:
                        if s.name == sensor_name:
                            matches.append(
                                self._build_sensor(
                                    s,
                                    repo_location_name=repo.location.name,
                                    repo_name=repo.name,
                                )
                            )
                if not matches:
                    raise DagsterPlusGraphqlError(f"Sensor not found: {sensor_name}")
                if len(matches) > 1:
                    origins = [s.repository_origin for s in matches]
                    raise DagsterPlusGraphqlError(
                        f"Multiple sensors found with name '{sensor_name}' in repositories: {', '.join(origins)}"
                    )

                return matches[0]
            case "RepositoryNotFoundError":
                raise DagsterPlusGraphqlError(f"Error listing repositories: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error listing repositories: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def _build_sensor(
        self,
        sensor: """ListSensorsSensorsOrErrorSensorsResults
        | ListRepositoriesWithSensorsRepositoriesOrErrorRepositoryConnectionNodesSensors 
        | GetSensorSensorOrErrorSensor""",
        *,
        repo_location_name: str,
        repo_name: str,
    ) -> DgApiSensor:
        return DgApiSensor(
            id=sensor.id,
            name=sensor.name,
            status=sensor.sensor_state.status,
            sensor_type=sensor.sensor_type,
            repository_origin=f"{repo_location_name}@{repo_name}",
            description=sensor.description,
            next_tick_timestamp=None,
        )
