from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, Optional

import click
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.cli.api.shared import (
    DgApiError,
    get_default_error_mapping,
    get_graphql_error_mappings,
)


class IGraphQLClient(ABC):
    """Abstract base class for GraphQL clients with execute method."""

    @abstractmethod
    def execute(self, query: str, variables: Optional[Mapping[str, Any]] = None) -> dict: ...


class DagsterPlusUnauthorizedError(click.ClickException):
    pass


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

    def execute(self, query: str, variables: Optional[Mapping[str, Any]] = None):
        # defer for import performance
        from gql import gql

        from dagster_dg_cli.cli.api.shared import get_graphql_error_types

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
