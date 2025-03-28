import json
from typing import Any

import responses


def mock_gql_response(
    query: str,
    json_data: dict[str, Any],
    url: str = "https://dagster.cloud/hooli/graphql",
) -> None:
    def match(request) -> tuple[bool, str]:
        request_body = request.body
        json_body = json.loads(request_body) if request_body else {}
        body_query_normalized = [line.strip() for line in json_body["query"].strip().split("\n")]
        query_normalized = [line.strip() for line in query.strip().split("\n")]
        neq_index = next(
            (i for i, (a, b) in enumerate(zip(body_query_normalized, query_normalized)) if a != b),
            None,
        )
        return (
            body_query_normalized == query_normalized,
            f"\n'{body_query_normalized[neq_index]}'\n!=\n'{query_normalized[neq_index]}'\n"
            if neq_index is not None
            else "",
        )

    responses.add(
        responses.POST,
        url,
        json=json_data,
        match=[match],
    )
