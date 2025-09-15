"""Run metadata API implementation."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_dg_cli.api_layer.graphql_adapter.run import get_run_via_graphql
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.run import DgApiRun


@dataclass(frozen=True)
class DgApiRunApi:
    """API for run metadata operations."""

    client: IGraphQLClient

    def get_run(self, run_id: str) -> "DgApiRun":
        """Get run metadata by ID."""
        return get_run_via_graphql(self.client, run_id)
