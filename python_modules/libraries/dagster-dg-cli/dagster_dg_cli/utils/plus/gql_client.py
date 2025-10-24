import json
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Optional

import click
from dagster_shared.plus.config import DagsterPlusCliConfig

if TYPE_CHECKING:
    from dagster_cloud_cli.commands.ci.state import LocationState


class IGraphQLClient(ABC):
    """Abstract base class for GraphQL clients with execute method."""

    @abstractmethod
    def execute(self, query: str, variables: Optional[Mapping[str, Any]] = None) -> dict: ...


class DagsterPlusUnauthorizedError(click.ClickException):
    pass


class DebugGraphQLClient(IGraphQLClient):
    """GraphQL client wrapper that logs queries and responses to stderr for debugging."""

    def __init__(self, wrapped_client: IGraphQLClient):
        self.wrapped_client = wrapped_client

    def execute(self, query: str, variables: Optional[Mapping[str, Any]] = None) -> dict:
        """Execute GraphQL query and log details to stderr."""
        # Print query details to stderr
        click.echo("=== GraphQL Query ===", err=True)
        click.echo(query, err=True)

        if variables:
            click.echo("=== Variables ===", err=True)
            click.echo(json.dumps(dict(variables), indent=2), err=True)

        # Execute the actual query
        result = self.wrapped_client.execute(query, variables)

        # Print response to stderr
        click.echo("=== Response ===", err=True)
        click.echo(json.dumps(result, indent=2), err=True)
        click.echo("=" * 20, err=True)

        return result


class DagsterPlusGraphQLClient(IGraphQLClient):
    def __init__(self, url: str, headers: Mapping[str, str]):
        # defer for import performance
        from gql import Client
        from gql.transport.requests import RequestsHTTPTransport

        self.client = Client(
            transport=RequestsHTTPTransport(url=url, use_json=True, headers=dict(headers))
        )

    @classmethod
    def from_config(cls, config: DagsterPlusCliConfig):
        return cls(
            url=f"{config.organization_url}/graphql",
            headers={
                k: v
                for k, v in {
                    "Dagster-Cloud-Api-Token": config.user_token,
                    "Dagster-Cloud-Organization": config.organization,
                    "Dagster-Cloud-Deployment": config.default_deployment,
                }.items()
                if v is not None
            },
        )

    @classmethod
    def from_location_state(
        cls, location_state: "LocationState", api_token: str, organization: str
    ):
        return cls(
            url=f"{location_state.url}/graphql",
            headers={
                "Dagster-Cloud-Api-Token": api_token,
                "Dagster-Cloud-Organization": organization,
                "Dagster-Cloud-Deployment": location_state.deployment_name,
            },
        )

    def execute(self, query: str, variables: Optional[Mapping[str, Any]] = None):
        # defer for import performance
        from gql import gql

        # Import error handling classes locally to avoid circular imports
        from dagster_dg_cli.cli.api.shared import (
            DgApiError,
            get_default_error_mapping,
            get_graphql_error_mappings,
            get_graphql_error_types,
        )

        result = self.client.execute(gql(query), variable_values=dict(variables or {}))
        value = next(iter(result.values()))
        if isinstance(value, Mapping):
            typename = value.get("__typename")
            if typename in get_graphql_error_types():
                message = value.get("message", "Unknown error")

                # Get mapping or use default
                mappings = get_graphql_error_mappings()
                mapping = (
                    mappings.get(typename, get_default_error_mapping())
                    if typename
                    else get_default_error_mapping()
                )

                raise DgApiError(
                    message=message,
                    code=mapping.code,
                    status_code=mapping.status_code,
                )
        return result
