"""Schedule endpoints - REST-like interface."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_dg_cli.api_layer.graphql_adapter.schedule import (
    get_dg_plus_api_schedule_via_graphql,
    list_dg_plus_api_schedules_via_graphql,
)
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.schedule import DgApiSchedule, DgApiScheduleList


@dataclass(frozen=True)
class DgApiScheduleApi:
    client: IGraphQLClient

    def list_schedules(self) -> "DgApiScheduleList":
        """List schedules."""
        return list_dg_plus_api_schedules_via_graphql(self.client)

    def get_schedule(self, schedule_name: str) -> "DgApiSchedule":
        """Get single schedule by name."""
        return get_dg_plus_api_schedule_via_graphql(self.client, schedule_name)
