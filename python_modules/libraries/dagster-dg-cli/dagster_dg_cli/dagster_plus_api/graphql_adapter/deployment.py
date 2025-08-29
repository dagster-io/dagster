"""GraphQL implementation for deployment operations."""

from typing import TYPE_CHECKING, Any, Optional

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


def process_deployments_response(graphql_response: dict[str, Any]) -> "DeploymentList":
    """Process GraphQL response into DeploymentList.

    This is a pure function that can be easily tested without mocking GraphQL clients.

    Args:
        graphql_response: Raw GraphQL response containing "fullDeployments"

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

    return DeploymentList(
        items=deployments,
        total=len(deployments),
    )


def list_deployments_via_graphql(
    client: DagsterPlusGraphQLClient,
    limit: Optional[int] = None,
) -> "DeploymentList":
    """Fetch deployments using GraphQL.
    This is an implementation detail that can be replaced with REST calls later.
    """
    result = client.execute(LIST_DEPLOYMENTS_QUERY)

    deployment_list = process_deployments_response(result)

    # Apply limit if specified
    if limit is not None:
        deployment_list.items = deployment_list.items[:limit]
        deployment_list.total = len(deployment_list.items)

    return deployment_list
