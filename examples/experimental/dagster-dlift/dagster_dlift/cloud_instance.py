from typing import Any, Iterator, Mapping, Sequence

import requests

from dagster_dlift.gql_queries import (
    GET_DBT_MODELS_QUERY,
    GET_DBT_SOURCES_QUERY,
    VERIFICATION_QUERY,
)

ENVIRONMENTS_SUBPATH = "environments/"


class DbtCloudInstance:
    def __init__(
        self,
        # Can be found on the Account Info page of dbt.
        account_id: str,
        # Can be either a personal token or a service token.
        token: str,
        # Can be found on the
        access_url: str,
        discovery_api_url: str,
    ):
        self.account_id = account_id
        self.token = token
        self.access_url = access_url
        self.discovery_api_url = discovery_api_url

    def get_api_v2_url(self) -> str:
        return f"{self.access_url}/api/v2/accounts/{self.account_id}"

    def get_discovery_api_url(self) -> str:
        return f"{self.discovery_api_url}/graphql"

    def get_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "Accept": "application/json",
                "Authorization": f"Token {self.token}",
            }
        )
        return session

    def make_access_api_request(self, subpath: str) -> Mapping[str, Any]:
        session = self.get_session()
        return self.ensure_valid_response(session.get(f"{self.get_api_v2_url()}/{subpath}")).json()

    def ensure_valid_response(self, response: requests.Response) -> requests.Response:
        if response.status_code != 200:
            raise Exception(f"Request to DBT Cloud failed: {response.text}")
        return response

    def make_discovery_api_query(self, query: str, variables: Mapping[str, Any]):
        session = self.get_session()
        return self.ensure_valid_response(
            session.post(
                self.get_discovery_api_url(),
                json={"query": query, "variables": variables},
            )
        ).json()

    def list_environment_ids(self) -> Sequence[int]:
        return [
            environment["id"]
            for environment in self.make_access_api_request(ENVIRONMENTS_SUBPATH)["data"]
        ]

    def get_environment_id_by_name(self, environment_name: str) -> int:
        return next(
            iter(
                [
                    environment["id"]
                    for environment in self.make_access_api_request(ENVIRONMENTS_SUBPATH)["data"]
                    if environment["name"] == environment_name
                ]
            )
        )

    def verify_connections(self) -> None:
        # Verifies connection to both the access and discovery APIs.
        for environment_id in self.list_environment_ids():
            response = self.make_discovery_api_query(
                VERIFICATION_QUERY, {"environmentId": environment_id}
            )
            try:
                if response["data"]["environment"]["__typename"] != "Environment":
                    raise Exception(
                        f"Failed to verify connection to environment {environment_id}. Response: {response}"
                    )
            except KeyError:
                raise Exception(
                    f"Failed to verify connection to environment {environment_id}. Response: {response}"
                )

    def definition_response_iterator(
        self, query: str, variables: Mapping[str, Any], key: str
    ) -> Iterator[Mapping[str, Any]]:
        page_size = 100
        start_cursor = None
        while response := self.make_discovery_api_query(
            query,
            {**variables, "first": page_size, "after": start_cursor},
        ):
            yield from response["data"]["environment"]["definition"][key]["edges"]
            if not response["data"]["environment"]["definition"][key]["pageInfo"]["hasNextPage"]:
                break
            start_cursor = response["data"]["environment"]["definition"][key]["pageInfo"][
                "endCursor"
            ]

    def get_dbt_models(self, environment_id: int) -> Sequence[Mapping[str, Any]]:
        return [
            model["node"]
            for model in self.definition_response_iterator(
                GET_DBT_MODELS_QUERY, {"environmentId": environment_id}, key="models"
            )
        ]

    def get_dbt_sources(self, environment_id: int) -> Sequence[Mapping[str, Any]]:
        return [
            source["node"]
            for source in self.definition_response_iterator(
                GET_DBT_SOURCES_QUERY, {"environmentId": environment_id}, key="sources"
            )
        ]
