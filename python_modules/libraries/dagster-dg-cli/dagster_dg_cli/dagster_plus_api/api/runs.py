"""Run endpoints - REST-like interface."""

from typing import TYPE_CHECKING, Optional

from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.dagster_plus_api.graphql_adapter.run import list_run_events_via_graphql

if TYPE_CHECKING:
    from dagster_dg_cli.dagster_plus_api.schemas.run import RunEventList


class DgApiRunApi:
    def __init__(self, config: DagsterPlusCliConfig):
        self.config = config

    def list_run_events(
        self,
        run_id: str,
        limit: Optional[int] = None,
        event_type: Optional[str] = None,
        step_key: Optional[str] = None,
    ) -> "RunEventList":
        return list_run_events_via_graphql(
            self.config, run_id=run_id, limit=limit, event_type=event_type, step_key=step_key
        )
