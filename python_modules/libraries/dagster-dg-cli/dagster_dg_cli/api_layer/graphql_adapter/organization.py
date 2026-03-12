"""GraphQL implementation for organization operations."""

from typing import TYPE_CHECKING, Any

from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.organization import OrganizationSettings

ORGANIZATION_SETTINGS_QUERY = """
query OrganizationSettings {
    organizationSettings {
        settings
    }
}
"""

SET_ORGANIZATION_SETTINGS_MUTATION = """
mutation SetOrganizationSettings($organizationSettings: OrganizationSettingsInput!) {
    setOrganizationSettings(organizationSettings: $organizationSettings) {
        __typename
        ... on OrganizationSettings {
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


def process_organization_settings_response(
    graphql_response: dict[str, Any],
) -> "OrganizationSettings":
    """Process GraphQL response into OrganizationSettings."""
    from dagster_dg_cli.api_layer.schemas.organization import OrganizationSettings

    return OrganizationSettings(settings=graphql_response.get("settings", {}))


def process_set_organization_settings_response(
    graphql_response: dict[str, Any],
) -> "OrganizationSettings":
    """Process GraphQL mutation response into OrganizationSettings."""
    from dagster_dg_cli.api_layer.schemas.organization import OrganizationSettings

    typename = graphql_response.get("__typename")

    if typename == "OrganizationSettings":
        return OrganizationSettings(settings=graphql_response.get("settings", {}))
    elif typename in ["UnauthorizedError", "PythonError"]:
        error_message = graphql_response.get("message", "Unknown error")
        raise ValueError(f"Error setting organization settings: {error_message}")
    else:
        raise ValueError(f"Unexpected response type: {typename}")


def get_organization_settings_via_graphql(
    client: IGraphQLClient,
) -> "OrganizationSettings":
    """Fetch organization settings using GraphQL."""
    result = client.execute(ORGANIZATION_SETTINGS_QUERY)
    settings_data = result.get("organizationSettings", {})
    return process_organization_settings_response(settings_data)


def set_organization_settings_via_graphql(
    client: IGraphQLClient,
    settings: dict[str, Any],
) -> "OrganizationSettings":
    """Set organization settings using GraphQL."""
    result = client.execute(
        SET_ORGANIZATION_SETTINGS_MUTATION,
        {"organizationSettings": {"settings": settings}},
    )
    return process_set_organization_settings_response(result)
