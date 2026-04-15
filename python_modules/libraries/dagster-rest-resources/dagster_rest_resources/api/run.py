"""Run metadata API implementation."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.graphql_adapter.run import get_run_via_graphql, list_runs_via_graphql

if TYPE_CHECKING:
    from dagster_rest_resources.schemas.run import DgApiRun, DgApiRunList


@dataclass(frozen=True)
class DgApiRunApi:
    """API for run metadata operations."""

    client: IGraphQLClient

    def get_run(self, run_id: str) -> "DgApiRun":
        """Get run metadata by ID."""
        return get_run_via_graphql(self.client, run_id)

    def list_runs(
        self,
        limit: int = 50,
        cursor: str | None = None,
        statuses: tuple[str, ...] = (),
        job_name: str | None = None,
    ) -> "DgApiRunList":
        """List runs with optional filtering."""
        return list_runs_via_graphql(
            self.client, limit=limit, cursor=cursor, statuses=statuses, job_name=job_name
        )
