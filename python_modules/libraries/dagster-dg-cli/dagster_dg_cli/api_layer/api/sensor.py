"""Sensor API implementation."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from dagster_dg_cli.api_layer.graphql_adapter.sensor import (
    get_sensor_via_graphql,
    list_sensors_via_graphql,
)
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.sensor import DgApiSensor, DgApiSensorList


@dataclass(frozen=True)
class DgApiSensorApi:
    """API for sensor operations."""

    client: IGraphQLClient

    def list_sensors(
        self,
        repository_location_name: Optional[str] = None,
        repository_name: Optional[str] = None,
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
        from dagster_dg_cli.api_layer.graphql_adapter.sensor import get_sensor_by_name_via_graphql

        return get_sensor_by_name_via_graphql(self.client, sensor_name=sensor_name)
