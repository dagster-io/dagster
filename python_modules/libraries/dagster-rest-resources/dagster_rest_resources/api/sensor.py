"""Sensor API implementation."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.graphql_adapter.sensor import (
    get_sensor_by_name_via_graphql,
    get_sensor_via_graphql,
    list_sensors_via_graphql,
)

if TYPE_CHECKING:
    from dagster_rest_resources.schemas.sensor import DgApiSensor, DgApiSensorList


@dataclass(frozen=True)
class DgApiSensorApi:
    """API for sensor operations."""

    client: IGraphQLClient

    def list_sensors(
        self,
        repository_location_name: str | None = None,
        repository_name: str | None = None,
    ) -> "DgApiSensorList":
        """List all sensors, optionally filtered by repository location and name."""
        return list_sensors_via_graphql(
            self.client,
            repository_location_name=repository_location_name,
            repository_name=repository_name,
        )

    def get_sensor(
        self,
        sensor_name: str,
        repository_location_name: str,
        repository_name: str,
    ) -> "DgApiSensor":
        """Get sensor by name and repository details."""
        return get_sensor_via_graphql(
            self.client,
            sensor_name=sensor_name,
            repository_location_name=repository_location_name,
            repository_name=repository_name,
        )

    def get_sensor_by_name(self, sensor_name: str) -> "DgApiSensor":
        """Get sensor by name, searching across all repositories."""
        return get_sensor_by_name_via_graphql(self.client, sensor_name=sensor_name)
