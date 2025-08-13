"""GraphQL implementation for deployment operations."""

from typing import TYPE_CHECKING, Optional

from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.dagster_plus_api.schemas.deployment import DeploymentList

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
) -> "DeploymentList":
    """Fetch deployments using GraphQL.
    This is an implementation detail that can be replaced with REST calls later.
    """
    # Import pydantic models only when needed
    from dagster_dg_cli.dagster_plus_api.schemas.deployment import (
        Deployment,
        DeploymentList,
        DeploymentType,
    )

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
