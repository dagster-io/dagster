"""Job API implementation."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_dg_cli.api_layer.graphql_adapter.job import list_jobs_via_graphql
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.job import DgApiJob, DgApiJobList


@dataclass(frozen=True)
class DgApiJobApi:
    """API for job operations."""

    client: IGraphQLClient

    def list_jobs(self) -> "DgApiJobList":
        """List all jobs."""
        return list_jobs_via_graphql(self.client)

    def get_job_by_name(self, job_name: str) -> "DgApiJob":
        """Get job by name, searching across all repositories."""
        from dagster_dg_cli.api_layer.graphql_adapter.job import get_job_by_name_via_graphql

        return get_job_by_name_via_graphql(self.client, job_name=job_name)
