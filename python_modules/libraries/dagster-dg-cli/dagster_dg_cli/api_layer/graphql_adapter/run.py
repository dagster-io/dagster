"""GraphQL adapter for run metadata."""

from typing import Any

from dagster_dg_cli.cli.api.shared import (
    DgApiError,
    get_default_error_mapping,
    get_graphql_error_mappings,
)
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

RUN_METADATA_QUERY = """
query DgApiRunMetadataQuery($runId: ID!) {
    runOrError(runId: $runId) {
        __typename
        ... on Run {
            id
            status
            creationTime
            startTime
            endTime
            pipelineName
            mode
        }
        ... on RunNotFoundError {
            message
        }
        ... on PythonError {
            message
            stack
        }
    }
}
"""


def get_run_via_graphql(client: IGraphQLClient, run_id: str) -> dict[str, Any]:
    """Get run metadata via GraphQL."""
    variables = {"runId": run_id}
    result = client.execute(RUN_METADATA_QUERY, variables)

    run_result = result.get("runOrError")
    if not run_result:
        raise DgApiError(
            message="Empty response from GraphQL API", code="INTERNAL_ERROR", status_code=500
        )

    typename = run_result.get("__typename")

    # Handle GraphQL errors
    error_mappings = get_graphql_error_mappings()
    if typename in error_mappings:
        mapping = error_mappings[typename]
        error_msg = run_result.get("message", f"Unknown error: {typename}")
        raise DgApiError(message=error_msg, code=mapping.code, status_code=mapping.status_code)

    if typename != "Run":
        # Unmapped error type
        mapping = get_default_error_mapping()
        error_msg = run_result.get("message", f"Unknown error: {typename}")
        raise DgApiError(message=error_msg, code=mapping.code, status_code=mapping.status_code)

    return run_result
