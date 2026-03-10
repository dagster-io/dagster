"""GraphQL implementation for deployment operations."""

from typing import TYPE_CHECKING, Any

from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.deployment import (
        Deployment,
        DeploymentList,
        DeploymentSettings,
    )

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

LIST_BRANCH_DEPLOYMENTS_QUERY = """
query ListBranchDeployments($limit: Int!, $pullRequestStatus: PullRequestStatus) {
    branchDeployments(limit: $limit, pullRequestStatus: $pullRequestStatus) {
        nodes {
            deploymentName
            deploymentId
            deploymentType
        }
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


GET_DEPLOYMENT_SETTINGS_QUERY = """
query GetDeploymentSettings {
    deploymentSettings {
        settings
    }
}
"""

SET_DEPLOYMENT_SETTINGS_MUTATION = """
mutation SetDeploymentSettings($deploymentSettings: GenericScalar!) {
    setDeploymentSettings(deploymentSettings: $deploymentSettings) {
        __typename
        ... on DeploymentSettings {
            settings
        }
        ... on UnauthorizedError {
            message
        }
        ... on PythonError {
            message
        }
    }
}
"""


def process_deployment_settings_response(graphql_response: dict[str, Any]) -> "DeploymentSettings":
    """Process GraphQL response into DeploymentSettings."""
    from dagster_dg_cli.api_layer.schemas.deployment import DeploymentSettings

    return DeploymentSettings(settings=graphql_response.get("settings", {}))


def process_set_deployment_settings_response(
    graphql_response: dict[str, Any],
) -> "DeploymentSettings":
    """Process GraphQL mutation response into DeploymentSettings."""
    from dagster_dg_cli.api_layer.schemas.deployment import DeploymentSettings

    typename = graphql_response.get("__typename")

    if typename == "DeploymentSettings":
        return DeploymentSettings(settings=graphql_response.get("settings", {}))
    elif typename in ["UnauthorizedError", "PythonError"]:
        error_message = graphql_response.get("message", "Unknown error")
        raise ValueError(f"Error setting deployment settings: {error_message}")
    else:
        raise ValueError(f"Unexpected response type: {typename}")


def get_deployment_settings_via_graphql(
    client: IGraphQLClient,
) -> "DeploymentSettings":
    """Fetch deployment settings using GraphQL."""
    result = client.execute(GET_DEPLOYMENT_SETTINGS_QUERY)
    # execute() returns {"deploymentSettings": {"settings": {...}}},
    # unwrap the top-level query key before processing
    settings_data = result.get("deploymentSettings", {})
    return process_deployment_settings_response(settings_data)


def set_deployment_settings_via_graphql(
    client: IGraphQLClient,
    settings: dict[str, Any],
) -> "DeploymentSettings":
    """Set deployment settings using GraphQL."""
    result = client.execute(
        SET_DEPLOYMENT_SETTINGS_MUTATION,
        {"deploymentSettings": settings},
    )
    return process_set_deployment_settings_response(result)


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
    limit: int | None = None,
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


def process_branch_deployments_response(graphql_response: dict[str, Any]) -> "DeploymentList":
    """Process GraphQL response for branch deployments into DeploymentList.

    Args:
        graphql_response: Raw GraphQL response from branchDeployments query,
            after execute() unwraps the top-level key. Contains {"nodes": [...]}.

    Returns:
        DeploymentList: Processed deployment data
    """
    from dagster_dg_cli.api_layer.schemas.deployment import (
        Deployment,
        DeploymentList,
        DeploymentType,
    )

    nodes = graphql_response.get("nodes", [])

    deployments = [
        Deployment(
            id=d["deploymentId"],
            name=d["deploymentName"],
            type=DeploymentType[d["deploymentType"]],
        )
        for d in nodes
    ]

    return DeploymentList(
        items=deployments,
        total=len(deployments),
    )


def list_branch_deployments_via_graphql(
    client: IGraphQLClient,
    limit: int | None = None,
    pull_request_status: str | None = None,
) -> "DeploymentList":
    """Fetch branch deployments using GraphQL."""
    variables: dict[str, Any] = {"limit": limit if limit is not None else 50}
    if pull_request_status is not None:
        variables["pullRequestStatus"] = pull_request_status

    result = client.execute(LIST_BRANCH_DEPLOYMENTS_QUERY, variables)

    # execute() returns {"branchDeployments": {"nodes": [...]}},
    # so we need to unwrap the top-level key
    branch_data = result.get("branchDeployments", {})
    return process_branch_deployments_response(branch_data)


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


DELETE_DEPLOYMENT_MUTATION = """
mutation CliDeleteDeployment($deploymentId: Int!) {
    deleteDeployment(deploymentId: $deploymentId) {
        __typename
        ... on DagsterCloudDeployment {
            deploymentId
            deploymentName
            deploymentType
        }
        ... on PythonError {
            message
        }
    }
}
"""


def process_delete_deployment_response(graphql_response: dict[str, Any]) -> "Deployment":
    """Process GraphQL delete mutation response into Deployment.

    The IGraphQLClient.execute() auto-raises on error __typename,
    so we only need to handle the success case here.

    Args:
        graphql_response: The inner deleteDeployment value after unwrapping.
    """
    from dagster_dg_cli.api_layer.schemas.deployment import Deployment, DeploymentType

    return Deployment(
        id=graphql_response["deploymentId"],
        name=graphql_response["deploymentName"],
        type=DeploymentType[graphql_response["deploymentType"]],
    )


def delete_deployment_via_graphql(
    client: IGraphQLClient,
    deployment_id: int,
) -> "Deployment":
    """Delete a deployment using GraphQL."""
    result = client.execute(DELETE_DEPLOYMENT_MUTATION, {"deploymentId": deployment_id})
    deployment_data = result.get("deleteDeployment", {})
    return process_delete_deployment_response(deployment_data)


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
