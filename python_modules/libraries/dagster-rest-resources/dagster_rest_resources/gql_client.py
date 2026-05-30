import json
from abc import ABC
from collections.abc import Callable, Mapping
from typing import Any

import httpx

from dagster_rest_resources.__generated__.client import Client as AriadneClient
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)


class IGraphQLClient(AriadneClient, ABC):
    """Base class for exposed graphql clients.

    Extends AriadneClient to support overriding behaviors (like the debug implementation)
    and custom queries that are not available as code-generated methods (via execute_arbitrary).
    """

    def __init__(
        self,
        *,
        url: str,
        api_token: str | None,
        organization: str | None,
        deployment: str | None,
        http_client: httpx.Client | None = None,
    ):
        headers = {
            k: v
            for k, v in {
                "Dagster-Cloud-Api-Token": api_token,
                "Dagster-Cloud-Organization": organization,
                "Dagster-Cloud-Deployment": deployment,
            }.items()
            if v is not None
        }
        http_client = http_client or httpx.Client(headers=headers, follow_redirects=True)
        super().__init__(
            url=f"{url.rstrip('/')}/graphql",
            headers=headers,
            http_client=http_client,
        )

    def execute_arbitrary(
        self,
        query: str,
        operation_name: str | None = None,
        variables: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = self.get_data(
            self.execute(
                query=query,
                operation_name=operation_name,
                variables=dict(variables) if variables else None,
            )
        )

        # extremely generic graphql error handling - since we don't know the queries being run by execute_arbitrary, the
        # best we can do for detecting graphql errors and raising them as python exceptions is this stringly-typed thing
        value = next(iter(data.values()))
        if isinstance(value, Mapping):
            typename = value.get("__typename", "")
            if typename == "UnauthorizedError":
                raise DagsterPlusUnauthorizedError("Unauthorized: " + value["message"])
            elif typename.endswith("Error"):
                raise DagsterPlusGraphqlError("Error: " + value["message"])

        return data


class DagsterPlusGraphQLClient(IGraphQLClient):
    pass


class DebugGraphQLClient(IGraphQLClient):
    """GraphQL client wrapper that logs queries and responses via a caller-supplied function."""

    __log: Callable[[str], None]

    def __init__(
        self,
        *,
        url: str,
        api_token: str | None,
        organization: str | None,
        deployment: str | None,
        log: Callable[[str], None],
        http_client: httpx.Client | None = None,
    ):
        super().__init__(
            url=url,
            api_token=api_token,
            organization=organization,
            deployment=deployment,
            http_client=http_client,
        )
        self.__log = log

    def execute(
        self,
        query: str,
        operation_name: str | None = None,
        variables: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        self.__log("=== GraphQL Query ===")
        self.__log(query)

        if operation_name:
            self.__log("=== Operation Name ===")
            self.__log(operation_name)

        if variables:
            self.__log("=== Variables ===")
            self.__log(json.dumps(variables, indent=2))

        return super().execute(query, operation_name, variables, **kwargs)

    def get_data(self, response: httpx.Response) -> dict[str, Any]:
        data = super().get_data(response)

        self.__log("=== Response ===")
        self.__log(json.dumps(data, indent=2))
        self.__log("=" * 20)

        return data
