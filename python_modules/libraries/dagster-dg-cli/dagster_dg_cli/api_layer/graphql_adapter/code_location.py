"""GraphQL implementation for code location operations."""

import json
from typing import TYPE_CHECKING, Any

from dagster_dg_cli.api_layer.schemas.code_location import (
    DgApiCodeLocation,
    DgApiCodeLocationList,
    DgApiCodeSource,
)
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.code_location import (
        DgApiAddCodeLocationResult,
        DgApiCodeLocationDocument,
        DgApiDeleteCodeLocationResult,
    )

LIST_CODE_LOCATIONS_QUERY = """
query CliWorkspaceEntries {
    workspace {
        workspaceEntries {
            locationName
            serializedDeploymentMetadata
        }
    }
}
"""

LOCATION_STATUSES_QUERY = """
query CliLocationStatuses {
    locationStatusesOrError {
        __typename
        ... on WorkspaceLocationStatusEntries {
            entries {
                name
                loadStatus
            }
        }
    }
}
"""


def process_location_statuses_response(graphql_response: dict[str, Any]) -> dict[str, str]:
    """Process GraphQL location statuses response into a name->loadStatus mapping."""
    statuses_or_error = graphql_response.get("locationStatusesOrError", {})
    typename = statuses_or_error.get("__typename")

    if typename != "WorkspaceLocationStatusEntries":
        return {}

    entries = statuses_or_error.get("entries", [])
    return {entry["name"]: entry["loadStatus"] for entry in entries}


def process_code_locations_response(
    graphql_response: dict[str, Any],
    statuses: dict[str, str] | None = None,
) -> "DgApiCodeLocationList":
    """Process GraphQL workspace entries response into DgApiCodeLocationList."""
    entries = graphql_response.get("workspace", {}).get("workspaceEntries", [])
    items: list[DgApiCodeLocation] = []

    for entry in entries:
        location_name = entry["locationName"]
        image: str | None = None
        code_source: DgApiCodeSource | None = None

        raw_metadata = entry.get("serializedDeploymentMetadata")
        if raw_metadata:
            metadata = json.loads(raw_metadata)
            image = metadata.get("image")
            python_file = metadata.get("python_file")
            module_name = metadata.get("module_name")
            package_name = metadata.get("package_name")
            autoload_defs_module_name = metadata.get("autoload_defs_module_name")
            if any([python_file, module_name, package_name, autoload_defs_module_name]):
                code_source = DgApiCodeSource(
                    python_file=python_file,
                    module_name=module_name,
                    package_name=package_name,
                    autoload_defs_module_name=autoload_defs_module_name,
                )

        status = statuses.get(location_name) if statuses else None

        items.append(
            DgApiCodeLocation(
                location_name=location_name,
                image=image,
                code_source=code_source,
                status=status,
            )
        )

    return DgApiCodeLocationList(items=items, total=len(items))


def fetch_location_statuses(client: IGraphQLClient) -> dict[str, str]:
    """Fetch location statuses and return a name->loadStatus mapping."""
    result = client.execute(LOCATION_STATUSES_QUERY, {})
    return process_location_statuses_response(result)


def list_code_locations_via_graphql(client: IGraphQLClient) -> "DgApiCodeLocationList":
    """List code locations using GraphQL."""
    result = client.execute(LIST_CODE_LOCATIONS_QUERY, {})
    statuses = fetch_location_statuses(client)
    return process_code_locations_response(result, statuses=statuses)


def get_code_location_via_graphql(
    client: IGraphQLClient,
    location_name: str,
) -> "DgApiCodeLocation | None":
    """Fetch a single code location by name using GraphQL.

    Since there's no single-location query, we fetch all and filter client-side.
    """
    location_list = list_code_locations_via_graphql(client)
    for location in location_list.items:
        if location.location_name == location_name:
            return location
    return None


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


DELETE_LOCATION_MUTATION = """
mutation CliDeleteLocation($locationName: String!) {
    deleteLocation(locationName: $locationName) {
        __typename
        ... on DeleteLocationSuccess {
            locationName
        }
        ... on PythonError {
            message
            stack
        }
        ... on UnauthorizedError {
            message
        }
    }
}
"""


def process_delete_location_response(
    graphql_response: dict[str, Any],
) -> "DgApiDeleteCodeLocationResult":
    """Process GraphQL response into DgApiDeleteCodeLocationResult."""
    from dagster_dg_cli.api_layer.schemas.code_location import DgApiDeleteCodeLocationResult

    typename = graphql_response.get("__typename")

    if typename == "DeleteLocationSuccess":
        return DgApiDeleteCodeLocationResult(
            location_name=graphql_response["locationName"],
        )
    elif typename in ["PythonError", "UnauthorizedError"]:
        error_message = graphql_response.get("message", "Unknown error")
        raise ValueError(f"Error deleting code location: {error_message}")
    else:
        raise ValueError(f"Unexpected response type: {typename}")


def delete_code_location_via_graphql(
    client: IGraphQLClient,
    location_name: str,
) -> "DgApiDeleteCodeLocationResult":
    """Delete a code location using GraphQL."""
    result = client.execute(
        DELETE_LOCATION_MUTATION,
        {"locationName": location_name},
    )
    response_data = result.get("deleteLocation", {})
    return process_delete_location_response(response_data)
