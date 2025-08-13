"""GraphQL implementation for deployment operations."""

from typing import TYPE_CHECKING, Any, Optional

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


def process_deployments_response(
    graphql_response: dict[str, Any], limit: Optional[int] = None
) -> "DeploymentList":
    """Process GraphQL response into DeploymentList.

    This is a pure function that can be easily tested without mocking GraphQL clients.

    Args:
        graphql_response: Raw GraphQL response containing "fullDeployments"
        limit: Optional limit to apply to results

    Returns:
        DeploymentList: Processed deployment data
    """
    # Import pydantic models only when needed
    from dagster_dg_cli.dagster_plus_api.schemas.deployment import (
        Deployment,
        DeploymentList,
        DeploymentType,
    )

    deployments_data = graphql_response.get("fullDeployments", [])

    deployments = [
        Deployment(
            id=d["deploymentId"],
            name=d["deploymentName"],
            type=DeploymentType[d["deploymentType"]],
        )
        for d in deployments_data
    ]

    # Apply limit if specified - GraphQL fullDeployments does not support limit parameter
    # so we must filter client-side
    if limit:
        deployments = deployments[:limit]

    return DeploymentList(
        items=deployments,
        total=len(deployments),
    )


def list_deployments_via_graphql(
    config: DagsterPlusCliConfig,
    limit: Optional[int] = None,
) -> "DeploymentList":
    """Fetch deployments using GraphQL.
    This is an implementation detail that can be replaced with REST calls later.
    """
    client = DagsterPlusGraphQLClient.from_config(config)
    result = client.execute(LIST_DEPLOYMENTS_QUERY)

    return process_deployments_response(result, limit=limit)
