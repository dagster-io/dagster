"""Run endpoints - REST-like interface."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from dagster_dg_cli.api_layer.graphql_adapter.run import get_run_via_graphql, list_runs_via_graphql
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.run import Run, RunList


@dataclass(frozen=True)
class DgApiRunApi:
    client: IGraphQLClient

    def list_runs(
        self,
        limit: Optional[int] = None,
        status: Optional[str] = None,
        job_name: Optional[str] = None,
        cursor: Optional[str] = None,
    ) -> "RunList":
        """List runs with optional filtering.

        Args:
            limit: Maximum number of runs to return
            status: Filter by run status
            job_name: Filter by job name
            cursor: Pagination cursor

        Returns:
            RunList: List of runs matching the filters
        """
        return list_runs_via_graphql(
            client=self.client,
            limit=limit,
            status=status,
            job_name=job_name,
            cursor=cursor,
        )

    def get_run(self, run_id: str) -> "Run":
        """Get a specific run by ID.

        Args:
            run_id: The run ID to fetch

        Returns:
            Run: The requested run

        Raises:
            Exception: If run not found or API error occurs
        """
        return get_run_via_graphql(client=self.client, run_id=run_id)
