"""Run metadata API implementation."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_dg_cli.api_layer.graphql_adapter.run import get_run_via_graphql
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.run import Run


@dataclass(frozen=True)
class DgApiRunApi:
    """API for run metadata operations."""

    client: IGraphQLClient

    def get_run(self, run_id: str) -> "Run":
        """Get run metadata by ID."""
        from dagster_dg_cli.api_layer.schemas.run import Run

        run_data = get_run_via_graphql(self.client, run_id)

        return Run(
            id=run_data["id"],
            status=run_data["status"],
            created_at=run_data["creationTime"],
            started_at=run_data.get("startTime"),
            ended_at=run_data.get("endTime"),
            pipeline_name=run_data.get("pipelineName"),
            mode=run_data.get("mode"),
        )
