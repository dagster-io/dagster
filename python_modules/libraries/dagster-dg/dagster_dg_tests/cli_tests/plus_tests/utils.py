import json
from typing import Any, Optional

import responses


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
