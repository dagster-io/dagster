"""Schedule API implementation."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from dagster_dg_cli.api_layer.graphql_adapter.schedule import (
    get_schedule_via_graphql,
    list_schedules_via_graphql,
)
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.schedule import DgApiSchedule, DgApiScheduleList


@dataclass(frozen=True)
class DgApiScheduleApi:
    """API for schedule operations."""

    client: IGraphQLClient

    def list_schedules(
        self,
        repository_location_name: Optional[str] = None,
        repository_name: Optional[str] = None,
    ) -> "DgApiScheduleList":
        """List all schedules, optionally filtered by code location and name."""
        return list_schedules_via_graphql(
            self.client,
            repository_location_name=repository_location_name,
            repository_name=repository_name,
        )

    def get_schedule(
        self,
        schedule_name: str,
        repository_location_name: str,
        repository_name: str,
    ) -> "DgApiSchedule":
        """Get schedule by name and code location details."""
        return get_schedule_via_graphql(
            self.client,
            schedule_name=schedule_name,
            repository_location_name=repository_location_name,
            repository_name=repository_name,
        )

    def get_schedule_by_name(self, schedule_name: str) -> "DgApiSchedule":
        """Get schedule by name, searching across all code locations."""
        from dagster_dg_cli.api_layer.graphql_adapter.schedule import (
            get_schedule_by_name_via_graphql,
        )

        return get_schedule_by_name_via_graphql(self.client, schedule_name=schedule_name)
