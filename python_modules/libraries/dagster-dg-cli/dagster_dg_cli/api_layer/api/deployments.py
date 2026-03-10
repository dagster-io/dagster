"""Deployment endpoints - REST-like interface."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_dg_cli.api_layer.graphql_adapter.deployment import (
    get_deployment_by_name_via_graphql,
    get_deployment_settings_via_graphql,
    list_deployments_via_graphql,
    set_deployment_settings_via_graphql,
)
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.deployment import (
        Deployment,
        DeploymentList,
        DeploymentSettings,
    )


@dataclass(frozen=True)
class DgApiDeploymentApi:
    client: IGraphQLClient

    def list_deployments(self) -> "DeploymentList":
        return list_deployments_via_graphql(self.client)

    def get_deployment(self, name: str) -> "Deployment":
        return get_deployment_by_name_via_graphql(self.client, name)

    def get_deployment_settings(self) -> "DeploymentSettings":
        return get_deployment_settings_via_graphql(self.client)

    def update_deployment_settings(self, settings: "DeploymentSettings") -> "DeploymentSettings":
        return set_deployment_settings_via_graphql(self.client, settings.settings)
