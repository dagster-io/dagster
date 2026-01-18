"""GraphQL implementation for deployment operations."""

from typing import TYPE_CHECKING, Any, Optional

from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.deployment import Deployment, DeploymentList

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

GET_DEPLOYMENT_QUERY = """
query GetDeployment($deploymentName: String!) {
    deploymentByName(name: $deploymentName) {
        __typename
        ... on DagsterCloudDeployment {
            deploymentName
            deploymentId
            deploymentType
        }
        ... on DeploymentNotFoundError {
            message
        }
        ... on PythonError {
            message
        }
        ... on UnauthorizedError {
            message
        }
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
    from dagster_dg_cli.api_layer.schemas.deployment import (
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
    client: IGraphQLClient,
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


def process_deployment_response(graphql_response: dict[str, Any]) -> "Deployment":
    """Process GraphQL response into single Deployment.

    This is a pure function that can be easily tested without mocking GraphQL clients.

    Args:
        graphql_response: Raw GraphQL response containing "deploymentByName"

    Returns:
        Deployment: Processed deployment data
    """
    # Import pydantic models only when needed
    from dagster_dg_cli.api_layer.schemas.deployment import Deployment, DeploymentType

    deployment_data = graphql_response.get("deploymentByName")

    if not deployment_data:
        raise ValueError("Deployment not found")

    # Handle union type response
    typename = deployment_data.get("__typename")

    if typename == "DagsterCloudDeployment":
        return Deployment(
            id=deployment_data["deploymentId"],
            name=deployment_data["deploymentName"],
            type=DeploymentType[deployment_data["deploymentType"]],
        )
    elif typename == "DeploymentNotFoundError":
        raise ValueError("Deployment not found")
    elif typename in ["PythonError", "UnauthorizedError"]:
        error_message = deployment_data.get("message", "Unknown error")
        raise ValueError(f"Error retrieving deployment: {error_message}")
    else:
        raise ValueError(f"Unexpected response type: {typename}")


def get_deployment_by_name_via_graphql(
    client: IGraphQLClient,
    name: str,
) -> "Deployment":
    """Fetch single deployment by name using GraphQL.
    This is an implementation detail that can be replaced with REST calls later.
    """
    variables = {"deploymentName": name}
    result = client.execute(GET_DEPLOYMENT_QUERY, variables)

    return process_deployment_response(result)
