"""Deployment endpoints - REST-like interface."""

from typing import TYPE_CHECKING

from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.dagster_plus_api.graphql_adapter.deployment import list_deployments_via_graphql

if TYPE_CHECKING:
    from dagster_dg_cli.dagster_plus_api.schemas.deployment import DeploymentList


class DgApiDeploymentApi:
    def __init__(self, config: DagsterPlusCliConfig):
        self.config = config

    def list_deployments(self) -> "DeploymentList":
        return list_deployments_via_graphql(self.config)
