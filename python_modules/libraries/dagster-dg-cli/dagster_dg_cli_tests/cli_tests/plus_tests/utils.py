import json
import sys
from typing import Any, Optional

import responses
from dagster_dg_cli.utils.plus import gql

PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"


def mock_gql_response(
    query: str,
    json_data: dict[str, Any],
    expected_variables: Optional[dict[str, Any]] = None,
    url: str = "https://dagster.cloud/hooli/graphql",
) -> None:
    def match(request) -> tuple[bool, str]:
        request_body = request.body
        json_body = json.loads(request_body) if request_body else {}

        # The gql library reformats queries, so we need to normalize both queries
        # Extract the operation name (e.g., "mutation CliCreateOrUpdateBranchDeployment")
        body_query = json_body.get("query", "").strip()
        expected_query = query.strip()

        # Compare operation name (first word + operation name)
        # e.g., "mutation CliCreateOrUpdateBranchDeployment" or "query DeploymentByNameQuery"
        body_parts = body_query.split("(")[0].strip().split()
        expected_parts = expected_query.split("(")[0].strip().split()

        # Match on operation type and name (e.g., "mutation CliCreateOrUpdateBranchDeployment")
        operation_matches = body_parts == expected_parts

        if expected_variables and json_body.get("variables") != expected_variables:
            return False, f"\n{json_body.get('variables')} != {expected_variables}\n{json_body}"

        return (
            operation_matches,
            f"\n'{' '.join(body_parts)}'\n!=\n'{' '.join(expected_parts)}'\n",
        )

    responses.add(
        responses.POST,
        url,
        json=json_data,
        match=[match],
    )


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
