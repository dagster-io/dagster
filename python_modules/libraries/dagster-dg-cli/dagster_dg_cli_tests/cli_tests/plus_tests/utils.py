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
        body_query_first_line_normalized = json_body["query"].strip().split("\n")[0].strip()
        query_first_line_normalized = query.strip().split("\n")[0].strip()
        if expected_variables and json_body.get("variables") != expected_variables:
            return False, f"\n{json_body.get('variables')} != {expected_variables}\n{json_body}"

        return (
            body_query_first_line_normalized == query_first_line_normalized,
            f"\n'{body_query_first_line_normalized}'\n!=\n'{query_first_line_normalized}'\n",
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
