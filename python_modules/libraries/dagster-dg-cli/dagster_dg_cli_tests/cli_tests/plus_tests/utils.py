import json
import sys
from collections.abc import Mapping
from typing import Any
from unittest.mock import patch

from dagster_dg_cli.utils.plus import gql

PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"

# Module-level
_patch_state: dict[str, Any] = {
    # queue of pending mock responses matched by _execute_arbitrary_side_effect.
    "_pending_mocks": [],
    # currently active patch of `IGraphQLClient.execute_arbitrary`
    "_active_patch": None,
}


def _execute_arbitrary_side_effect(
    query: str,
    operation_name: str | None = None,
    variables: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    from dagster_rest_resources.gql_client import (
        DagsterPlusGraphqlError,
        DagsterPlusUnauthorizedError,
    )

    query_first_line = query.strip().split("\n")[0].strip()

    # Iterate in reverse so the most recently registered mock wins.
    # Mocks are not consumed after use — so the same mock can match
    # across multiple command invocations within a test.
    for mock_entry in reversed(_patch_state["_pending_mocks"]):
        mock_query_first_line = mock_entry["query"].strip().split("\n")[0].strip()
        if mock_query_first_line != query_first_line:
            continue
        if mock_entry["expected_variables"] is not None:
            actual_vars = dict(variables) if variables else {}
            if actual_vars != mock_entry["expected_variables"]:
                continue
        inner_data = mock_entry["inner_data"]

        # Replicate IGraphQLClient.get_data error-handling so error tests still work.
        if inner_data:
            value = next(iter(inner_data.values()))
            if isinstance(value, Mapping):
                if value.get("__typename") == "UnauthorizedError":
                    raise DagsterPlusUnauthorizedError("Unauthorized: " + value["message"])
                elif value.get("__typename", "").endswith("Error"):
                    raise DagsterPlusGraphqlError("Error: " + value["message"])

        return inner_data

    raise AssertionError(
        f"No matching mock response for query starting with: {query_first_line!r}\n"
        f"variables: {variables}\n"
        f"Pending mocks: {[m['query'].strip().split(chr(10))[0].strip() for m in _patch_state['_pending_mocks']]}"
    )


def mock_gql_response(
    query: str,
    json_data: dict[str, Any],
    expected_variables: dict[str, Any] | None = None,
    url: str = "https://dagster.cloud/hooli/graphql",  # kept for API compatibility, unused
) -> None:
    # Strip the outer {"data": ...} wrapper — execute_arbitrary returns the inner dict.
    inner_data = json_data.get("data", json_data)
    _patch_state["_pending_mocks"].append(
        {
            "query": query,
            "inner_data": inner_data,
            "expected_variables": expected_variables,
        }
    )

    # Start the patch lazily on the first registered mock.
    if _patch_state["_active_patch"] is None:
        _patch_state["_active_patch"] = patch(
            "dagster_rest_resources.gql_client.IGraphQLClient.execute_arbitrary",
            side_effect=_execute_arbitrary_side_effect,
        )
        _patch_state["_active_patch"].start()


def cleanup_gql_mocks() -> None:
    """Stop any active IGraphQLClient.execute_arbitrary patch and clear pending mocks.

    Called automatically by the autouse fixture in conftest.py after each test.
    """
    _patch_state["_pending_mocks"].clear()
    if _patch_state["_active_patch"] is not None:
        _patch_state["_active_patch"].stop()
        _patch_state["_active_patch"] = None


def mock_serverless_response():
    mock_gql_response(
        query=gql.DEPLOYMENT_INFO_QUERY,
        json_data={
            "data": {
                "currentDeployment": {"agentType": "SERVERLESS"},
                "agents": [
                    {
                        "status": "NOT_RUNNING",
                        "metadata": [
                            {"key": "type", "value": json.dumps("ServerlessUserCodeLauncher")}
                        ],
                    },
                    {
                        "status": "RUNNING",
                        "metadata": [
                            {"key": "type", "value": json.dumps("ServerlessUserCodeLauncher")}
                        ],
                    },
                ],
            }
        },
    )


def mock_hybrid_response(agent_class="K8sUserCodeLauncher"):
    mock_gql_response(
        query=gql.DEPLOYMENT_INFO_QUERY,
        json_data={
            "data": {
                "currentDeployment": {"agentType": "HYBRID"},
                "agents": [
                    {
                        "status": "NOT_RUNNING",
                        "metadata": [{"key": "type", "value": json.dumps(agent_class)}],
                    },
                    {
                        "status": "RUNNING",
                        "metadata": [{"key": "type", "value": json.dumps(agent_class)}],
                    },
                ],
            }
        },
    )
