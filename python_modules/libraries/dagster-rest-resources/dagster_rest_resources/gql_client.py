import json
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from dagster_shared.plus.config import DagsterPlusCliConfig
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

if TYPE_CHECKING:
    from dagster_cloud_cli.commands.ci.state import LocationState


class IGraphQLClient(ABC):
    """Abstract base class for GraphQL clients with execute method."""

    @abstractmethod
    def execute(self, query: str, variables: Mapping[str, Any] | None = None) -> dict: ...


class DagsterPlusUnauthorizedError(Exception):
    pass


class DagsterPlusGraphqlError(Exception):
    pass


class DebugGraphQLClient(IGraphQLClient):
    """GraphQL client wrapper that logs queries and responses via a caller-supplied function."""

    __wrapped_client: IGraphQLClient
    __log: Callable[[str], None]

    def __init__(self, wrapped_client: IGraphQLClient, log: Callable[[str], None]):
        self.__wrapped_client = wrapped_client
        self.__log = log

    def execute(self, query: str, variables: Mapping[str, Any] | None = None) -> dict:
        self.__log("=== GraphQL Query ===")
        self.__log(query)

        if variables:
            self.__log("=== Variables ===")
            self.__log(json.dumps(dict(variables), indent=2))

        result = self.__wrapped_client.execute(query, variables)

        self.__log("=== Response ===")
        self.__log(json.dumps(result, indent=2))
        self.__log("=" * 20)

        return result


class DagsterPlusGraphQLClient(IGraphQLClient):
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

    def execute(self, query: str, variables: Mapping[str, Any] | None = None):
        result = self.client.execute(gql(query), variable_values=dict(variables or {}))
        value = next(iter(result.values()))
        if isinstance(value, Mapping):
            if value.get("__typename") == "UnauthorizedError":
                raise DagsterPlusUnauthorizedError("Unauthorized: " + value["message"])
            elif value.get("__typename", "").endswith("Error"):
                raise DagsterPlusGraphqlError("Error: " + value["message"])
        return result
