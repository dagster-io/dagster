"""Deployment endpoints - REST-like interface."""

from typing import Optional

from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.dagster_plus_api.graphql_adapter.deployment import list_deployments_via_graphql
from dagster_dg_cli.dagster_plus_api.schemas.deployment import DeploymentList


class DeploymentAPI:
    """Deployment API matching future FastAPI endpoints.
    This is the interface that will remain stable when we switch from GraphQL to REST.
    """

    def __init__(self, config: DagsterPlusCliConfig):
        self.config = config

    def list_deployments(
        self,
        limit: Optional[int] = None,
    ) -> DeploymentList:
        """GET /api/v1/deployments
        List all deployments in the organization.
        """
        return list_deployments_via_graphql(self.config, limit=limit)
