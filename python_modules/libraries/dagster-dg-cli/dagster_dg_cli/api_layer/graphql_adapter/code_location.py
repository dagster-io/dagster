"""GraphQL implementation for code location operations."""

from typing import TYPE_CHECKING, Any

from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.code_location import (
        DgApiAddCodeLocationResult,
        DgApiCodeLocationDocument,
    )

ADD_OR_UPDATE_LOCATION_FROM_DOCUMENT_MUTATION = """
mutation CliAddOrUpdateLocation($document: GenericScalar!) {
    addOrUpdateLocationFromDocument(document: $document) {
        __typename
        ... on WorkspaceEntry {
            locationName
        }
        ... on PythonError {
            message
            stack
        }
        ... on InvalidLocationError {
            errors
        }
        ... on UnauthorizedError {
            message
        }
    }
}
"""


def process_add_location_response(graphql_response: dict[str, Any]) -> "DgApiAddCodeLocationResult":
    """Process GraphQL response into DgApiAddCodeLocationResult."""
    from dagster_dg_cli.api_layer.schemas.code_location import DgApiAddCodeLocationResult

    typename = graphql_response.get("__typename")

    if typename == "WorkspaceEntry":
        return DgApiAddCodeLocationResult(
            location_name=graphql_response["locationName"],
        )
    elif typename == "InvalidLocationError":
        errors = graphql_response.get("errors", [])
        raise ValueError("Invalid location config:\n" + "\n".join(errors))
    elif typename in ["PythonError", "UnauthorizedError"]:
        error_message = graphql_response.get("message", "Unknown error")
        raise ValueError(f"Error adding code location: {error_message}")
    else:
        raise ValueError(f"Unexpected response type: {typename}")


def add_code_location_via_graphql(
    client: IGraphQLClient,
    document: "DgApiCodeLocationDocument",
) -> "DgApiAddCodeLocationResult":
    """Add or update a code location using GraphQL."""
    result = client.execute(
        ADD_OR_UPDATE_LOCATION_FROM_DOCUMENT_MUTATION,
        {"document": document.to_document_dict()},
    )
    response_data = result.get("addOrUpdateLocationFromDocument", {})
    return process_add_location_response(response_data)
