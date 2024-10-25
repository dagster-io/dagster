from typing import Any, Mapping, NamedTuple, Sequence

from dagster_dlift.cloud_instance import DbtCloudInstance


class ExpectedDiscoveryApiRequest(NamedTuple):
    query: str
    variables: Mapping[str, Any]

    def __hash__(self) -> int:
        return hash((self.query, frozenset(self.variables.items())))


class ExpectedAccessApiRequest(NamedTuple):
    subpath: str

    def __hash__(self) -> int:
        return hash(self.subpath)


class DbtCloudInstanceFake(DbtCloudInstance):
    """A version that allows users to fake API responses for testing purposes."""

    def __init__(
        self,
        access_api_responses: Mapping[ExpectedAccessApiRequest, Any],
        discovery_api_responses: Mapping[ExpectedDiscoveryApiRequest, Any],
    ):
        self.access_api_responses = access_api_responses
        self.discovery_api_responses = discovery_api_responses

    def make_access_api_request(self, subpath: str) -> Mapping[str, Any]:
        if ExpectedAccessApiRequest(subpath) not in self.access_api_responses:
            raise Exception(
                f"ExpectedAccessApiRequest({subpath}) not found in access_api_responses"
            )
        return self.access_api_responses[ExpectedAccessApiRequest(subpath)]

    def make_discovery_api_query(
        self, query: str, variables: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        if ExpectedDiscoveryApiRequest(query, variables) not in self.discovery_api_responses:
            raise Exception(
                f"ExpectedDiscoveryApiRequest({query}, {variables}) not found in discovery_api_responses"
            )
        return self.discovery_api_responses[ExpectedDiscoveryApiRequest(query, variables)]


def build_model_response(
    unique_id: str, parents: Sequence[str], has_next_page: bool = False, start_cursor: int = 0
) -> Mapping[str, Any]:
    return {
        "data": {
            "environment": {
                "definition": {
                    "models": {
                        "pageInfo": {"hasNextPage": has_next_page, "endCursor": start_cursor + 1},
                        "edges": [
                            {
                                "node": {
                                    "uniqueId": unique_id,
                                    "parents": [{"uniqueId": parent} for parent in parents],
                                }
                            },
                        ],
                    }
                }
            }
        }
    }
