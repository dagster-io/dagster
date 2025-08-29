"""Deployment endpoints - REST-like interface."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_dg_cli.dagster_plus_api.graphql_adapter.deployment import list_deployments_via_graphql
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.dagster_plus_api.schemas.deployment import DeploymentList


@dataclass(frozen=True)
class DgApiDeploymentApi:
    client: IGraphQLClient

    def list_deployments(self) -> "DeploymentList":
        return list_deployments_via_graphql(self.client)
