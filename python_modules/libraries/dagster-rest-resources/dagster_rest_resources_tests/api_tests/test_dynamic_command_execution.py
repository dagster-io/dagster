import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from dagster_rest_resources.gql_client import DagsterPlusGraphQLClient


class ReplayClient(DagsterPlusGraphQLClient):
    """GraphQL client that replays recorded responses."""

    def __init__(self, responses: list[dict[str, Any]]):
        # Don't call super().__init__ as we don't need the real GraphQL client
        self.responses = responses
        self.call_index = 0

    def execute(self, query: str, variables: Mapping[str, Any] | None = None) -> dict:
        """Return next recorded response."""
        if self.call_index >= len(self.responses):
            raise ValueError(f"Exhausted {len(self.responses)} responses")
        response = self.responses[self.call_index]
        self.call_index += 1
        return response


def load_recorded_graphql_responses(domain: str, scenario_name: str) -> list[dict[str, Any]]:
    """Load GraphQL response recordings for a given domain and scenario."""
    scenario_folder = Path(__file__).parent / f"{domain}_tests" / "recordings" / scenario_name

    if not scenario_folder.exists():
        raise ValueError(f"Recording scenario not found: {scenario_folder}")

    json_files = sorted([f for f in scenario_folder.glob("*.json") if f.name[0:2].isdigit()])

    if not json_files:
        raise ValueError(f"No numbered JSON files found in {scenario_folder}")

    responses = []
    for json_file in json_files:
        with open(json_file) as f:
            responses.append(json.load(f))

    return responses
