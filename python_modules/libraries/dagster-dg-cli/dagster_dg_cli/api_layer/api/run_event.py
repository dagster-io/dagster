"""Run events API implementation."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from dagster_dg_cli.api_layer.graphql_adapter.run_event import get_run_events_via_graphql
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.run_event import RunEventList


@dataclass(frozen=True)
class DgApiRunEventApi:
    """API for run events operations."""

    client: IGraphQLClient

    def get_events(
        self,
        run_id: str,
        event_type: Optional[str] = None,
        step_key: Optional[str] = None,
        limit: int = 100,
        after_cursor: Optional[str] = None,
    ) -> "RunEventList":
        """Get run events with filtering options."""
        from dagster_dg_cli.api_layer.schemas.run_event import RunEvent, RunEventLevel, RunEventList

        events_data = get_run_events_via_graphql(
            self.client,
            run_id=run_id,
            limit=limit,
            after_cursor=after_cursor,
            event_type=event_type,
            step_key=step_key,
        )

        # Convert to Pydantic models
        events = [
            RunEvent(
                run_id=e["runId"],
                message=e["message"],
                timestamp=e["timestamp"],
                level=RunEventLevel[e["level"]],
                step_key=e.get("stepKey"),
                event_type=e["eventType"],
            )
            for e in events_data["events"]
        ]

        return RunEventList(
            items=events,
            total=len(events),
            cursor=events_data.get("cursor"),
            has_more=events_data.get("hasMore", False),
        )
