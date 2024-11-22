from typing import AbstractSet, Any, Dict, Mapping, NamedTuple, Optional

from dagster_dlift.client import UnscopedDbtCloudClient
from dagster_dlift.translator import DbtCloudContentType


class ExpectedDiscoveryApiRequest(NamedTuple):
    query: str
    variables: Mapping[str, Any]

    def __hash__(self) -> int:
        return hash((self.query, frozenset(self.variables.items())))


class ExpectedAccessApiRequest(NamedTuple):
    subpath: str
    params: Optional[Mapping[str, Any]] = None

    def __hash__(self) -> int:
        return hash((self.subpath, frozenset(self.params.items() if self.params else [])))


class DbtCloudClientFake(UnscopedDbtCloudClient):
    """A version that allows users to fake API responses for testing purposes."""

    def __init__(
        self,
        access_api_responses: Mapping[ExpectedAccessApiRequest, Any],
        discovery_api_responses: Mapping[ExpectedDiscoveryApiRequest, Any],
    ):
        self.access_api_responses = access_api_responses
        self.discovery_api_responses = discovery_api_responses

    def make_access_api_request(
        self, subpath: str, params: Optional[Mapping[str, Any]] = None
    ) -> Mapping[str, Any]:
        expected_request = ExpectedAccessApiRequest(subpath, params)
        if expected_request not in self.access_api_responses:
            raise Exception(
                f"ExpectedAccessApiRequest({subpath}) not found in access_api_responses"
            )
        return self.access_api_responses[expected_request]

    def make_discovery_api_query(
        self, query: str, variables: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        if ExpectedDiscoveryApiRequest(query, variables) not in self.discovery_api_responses:
            raise Exception(
                f"ExpectedDiscoveryApiRequest({query}, {variables}) not found in discovery_api_responses"
            )
        return self.discovery_api_responses[ExpectedDiscoveryApiRequest(query, variables)]


def build_definition_response(inner: Mapping[str, Any]) -> Mapping[str, Any]:
    return {"data": {"environment": {"definition": inner}}}


def build_edge(unique_id: str, parents: Optional[AbstractSet[str]] = None) -> Mapping[str, Any]:
    node_dict: dict[str, Any] = {"uniqueId": unique_id}
    if parents is not None:
        node_dict["parents"] = [{"uniqueId": parent, "resourceType": "model"} for parent in parents]
    return {"node": node_dict}


def build_page_info(has_next_page: bool = False, start_cursor: int = 0) -> Mapping[str, Any]:
    return {"hasNextPage": has_next_page, "endCursor": start_cursor + 1}


def build_response_for_type(
    content_type: DbtCloudContentType,
    unique_id: str,
    parents: Optional[AbstractSet[str]] = None,
    has_next_page: bool = False,
    start_cursor: int = 0,
) -> Mapping[str, Any]:
    # plural lowercase string. IE "models", "sources", "tests"
    content_type_gql_str = f"{content_type.value.lower()}s"
    return build_definition_response(
        {
            content_type_gql_str: {
                "pageInfo": build_page_info(has_next_page, start_cursor),
                "edges": [build_edge(unique_id, parents)],
            }
        }
    )
