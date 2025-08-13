"""GraphQL implementation for deployment operations."""

from typing import Optional

from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.dagster_plus_api.schemas.deployment import (
    Deployment,
    DeploymentList,
    DeploymentType,
)
from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient

# GraphQL queries
LIST_DEPLOYMENTS_QUERY = """
query ListDeployments {
    fullDeployments {
        deploymentName
        deploymentId
        deploymentType
    }
}
"""


def list_deployments_via_graphql(
    config: DagsterPlusCliConfig,
    limit: Optional[int] = None,
) -> DeploymentList:
    """Fetch deployments using GraphQL.
    This is an implementation detail that can be replaced with REST calls later.
    """
    client = DagsterPlusGraphQLClient.from_config(config)
    result = client.execute(LIST_DEPLOYMENTS_QUERY)

    deployments_data = result.get("fullDeployments", [])

    deployments = [
        Deployment(
            id=d["deploymentId"],
            name=d["deploymentName"],
            type=DeploymentType[d["deploymentType"]],
        )
        for d in deployments_data
    ]

    # Apply limit if specified
    if limit:
        deployments = deployments[:limit]

    return DeploymentList(
        items=deployments,
        total=len(deployments),
    )
