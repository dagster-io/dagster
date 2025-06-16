from collections.abc import Mapping
from typing import Any, Optional

import click
from dagster_shared.plus.config import DagsterPlusCliConfig


class DagsterPlusUnauthorizedError(click.ClickException):
    pass


class DagsterPlusGraphQLClient:
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

        result = self.client.execute(gql(query), variable_values=dict(variables or {}))
        value = next(iter(result.values()))
        if isinstance(value, Mapping):
            if value.get("__typename") == "UnauthorizedError":
                raise DagsterPlusUnauthorizedError("Unauthorized: " + value["message"])
            elif value.get("__typename", "").endswith("Error"):
                raise click.ClickException("Error: " + value["message"])
        return result
