"""Tick API implementation."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_dg_cli.api_layer.graphql_adapter.tick import (
    get_schedule_ticks_via_graphql,
    get_sensor_ticks_via_graphql,
)
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.tick import DgApiTickList


@dataclass(frozen=True)
class DgApiTickApi:
    """API for tick operations."""

    client: IGraphQLClient

    def get_sensor_ticks(
        self,
        *,
        sensor_name: str,
        limit: int = 25,
        cursor: str | None = None,
        statuses: tuple[str, ...] = (),
        before_timestamp: float | None = None,
        after_timestamp: float | None = None,
    ) -> "DgApiTickList":
        """Get ticks for a sensor."""
        return get_sensor_ticks_via_graphql(
            self.client,
            sensor_name=sensor_name,
            limit=limit,
            cursor=cursor,
            statuses=statuses,
            before_timestamp=before_timestamp,
            after_timestamp=after_timestamp,
        )

    def get_schedule_ticks(
        self,
        *,
        schedule_name: str,
        limit: int = 25,
        cursor: str | None = None,
        statuses: tuple[str, ...] = (),
        before_timestamp: float | None = None,
        after_timestamp: float | None = None,
    ) -> "DgApiTickList":
        """Get ticks for a schedule."""
        return get_schedule_ticks_via_graphql(
            self.client,
            schedule_name=schedule_name,
            limit=limit,
            cursor=cursor,
            statuses=statuses,
            before_timestamp=before_timestamp,
            after_timestamp=after_timestamp,
        )
