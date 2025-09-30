"""GraphQL implementation for secret operations."""

from typing import TYPE_CHECKING, Any, Optional

from dagster_dg_cli.utils.plus.gql import (
    GET_SECRETS_FOR_SCOPES_QUERY,
    GET_SECRETS_FOR_SCOPES_QUERY_NO_VALUE,
)
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.secret import (
        DgApiSecret,
        DgApiSecretList,
        DgApiSecretScopesInput,
    )


def process_secrets_response(graphql_response: dict[str, Any]) -> "DgApiSecretList":
    """Process GraphQL response into DgApiSecretList.

    This is a pure function that can be easily tested without mocking GraphQL clients.

    Args:
        graphql_response: Raw GraphQL response containing secretsOrError

    Returns:
        DgApiSecretList: Processed secrets data

    Raises:
        ValueError: If GraphQL response contains errors
    """
    # Import pydantic models only when needed
    from dagster_dg_cli.api_layer.schemas.secret import DgApiSecret, DgApiSecretList

    secrets_or_error = graphql_response.get("secretsOrError")
    if not secrets_or_error:
        return DgApiSecretList(items=[], total=0)

    # Handle GraphQL error responses
    if secrets_or_error.get("__typename") == "UnauthorizedError":
        raise ValueError(f"Unauthorized: {secrets_or_error.get('message', 'Access denied')}")

    if secrets_or_error.get("__typename") == "PythonError":
        error_msg = secrets_or_error.get("message", "Unknown error")
        raise ValueError(f"Server error: {error_msg}")

    # Extract secrets array
    secrets_data = secrets_or_error.get("secrets", [])

    secrets = []
    for secret_data in secrets_data:
        # Convert GraphQL response to DgApiSecret model using field aliases
        secret = DgApiSecret.model_validate(secret_data)
        secrets.append(secret)

    return DgApiSecretList(
        items=secrets,
        total=len(secrets),
    )


def process_single_secret_response(
    graphql_response: dict[str, Any], secret_name: str
) -> "DgApiSecret":
    """Process GraphQL response for a single secret.

    Args:
        graphql_response: Raw GraphQL response
        secret_name: Name of the requested secret

    Returns:
        DgApiSecret: Single secret data

    Raises:
        ValueError: If secret not found or response contains errors
    """
    secret_list = process_secrets_response(graphql_response)

    if not secret_list.items:
        raise ValueError(f"Secret '{secret_name}' not found")

    if len(secret_list.items) > 1:
        # This shouldn't happen with secretName filter, but handle it
        matching_secrets = [s for s in secret_list.items if s.name == secret_name]
        if not matching_secrets:
            raise ValueError(f"Secret '{secret_name}' not found")
        return matching_secrets[0]

    return secret_list.items[0]


def build_secret_scopes_input(scope: Optional[str] = None) -> "DgApiSecretScopesInput":
    """Build SecretScopesInput based on scope parameter.

    Args:
        scope: Optional scope filter ("deployment" or "organization")

    Returns:
        DgApiSecretScopesInput: Scopes configuration for GraphQL query
    """
    from dagster_dg_cli.api_layer.schemas.secret import DgApiSecretScopesInput

    if scope == "deployment":
        # For deployment scope, include both full deployment and local deployment
        return DgApiSecretScopesInput(
            fullDeploymentScope=True,
            localDeploymentScope=True,
        )
    elif scope == "organization":
        # For organization scope, include all scopes
        return DgApiSecretScopesInput(
            fullDeploymentScope=True,
            allBranchDeploymentsScope=True,
            localDeploymentScope=True,
        )
    else:
        # Default: include all scopes
        return DgApiSecretScopesInput(
            fullDeploymentScope=True,
            allBranchDeploymentsScope=True,
            localDeploymentScope=True,
        )


def list_secrets_via_graphql(
    client: IGraphQLClient,
    location_name: Optional[str] = None,
    scope: Optional[str] = None,
    include_values: bool = False,
    limit: Optional[int] = None,
) -> "DgApiSecretList":
    """Fetch secrets using GraphQL.

    Args:
        client: GraphQL client
        location_name: Optional filter by code location
        scope: Optional scope filter ("deployment" or "organization")
        include_values: Whether to include secret values (security sensitive)
        limit: Optional limit on number of results

    Returns:
        DgApiSecretList: List of secrets

    Raises:
        ValueError: If GraphQL query fails or returns errors
    """
    scopes_input = build_secret_scopes_input(scope)

    # Choose query based on whether values should be included
    if include_values:
        query = GET_SECRETS_FOR_SCOPES_QUERY
    else:
        query = GET_SECRETS_FOR_SCOPES_QUERY_NO_VALUE

    variables: dict[str, Any] = {
        "scopes": scopes_input.to_dict(),
    }

    if location_name:
        variables["locationName"] = location_name

    result = client.execute(query, variables)

    secret_list = process_secrets_response(result)

    # Apply limit if specified
    if limit is not None:
        secret_list.items = secret_list.items[:limit]
        secret_list.total = len(secret_list.items)

    return secret_list


def get_secret_via_graphql(
    client: IGraphQLClient,
    secret_name: str,
    location_name: Optional[str] = None,
    include_value: bool = False,
) -> "DgApiSecret":
    """Fetch a specific secret using GraphQL.

    Args:
        client: GraphQL client
        secret_name: Name of the secret to fetch
        location_name: Optional filter by code location
        include_value: Whether to include secret value (security sensitive)

    Returns:
        DgApiSecret: Single secret

    Raises:
        ValueError: If secret not found or GraphQL query fails
    """
    # For get operations, we include all scopes to find the secret
    scopes_input = build_secret_scopes_input(scope=None)

    # Choose query based on whether value should be included
    if include_value:
        query = GET_SECRETS_FOR_SCOPES_QUERY
    else:
        query = GET_SECRETS_FOR_SCOPES_QUERY_NO_VALUE

    variables = {
        "scopes": scopes_input.to_dict(),
        "secretName": secret_name,
    }

    if location_name:
        variables["locationName"] = location_name

    result = client.execute(query, variables)

    return process_single_secret_response(result, secret_name)
