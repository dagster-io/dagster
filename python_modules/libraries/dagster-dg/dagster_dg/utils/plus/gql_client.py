from collections.abc import Mapping
from typing import Any, Optional

import click
from dagster_shared.plus.config import DagsterPlusCliConfig
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport


class DagsterCloudGraphQLClient:
    def __init__(self, url: str, headers: Mapping[str, str]):
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
        result = self.client.execute(gql(query), variable_values=dict(variables or {}))
        value = next(iter(result.values()))
        if isinstance(value, Mapping):
            if value.get("__typename") == "UnauthorizedError":
                raise click.ClickException("Unauthorized: " + value["message"])
            elif value.get("__typename", "").endswith("Error"):
                raise click.ClickException("Error: " + value["message"])
        return result
