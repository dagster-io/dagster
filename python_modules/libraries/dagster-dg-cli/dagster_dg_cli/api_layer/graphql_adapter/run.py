"""GraphQL adapter for run metadata."""

from dagster_dg_cli.api_layer.schemas.run import DgApiRun, DgApiRunStatus
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

RUN_METADATA_QUERY = """
query DgApiRunMetadataQuery($runId: ID!) {
    runOrError(runId: $runId) {
        __typename
        ... on Run {
            id
            runId
            status
            creationTime
            startTime
            endTime
            jobName
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


def get_run_via_graphql(client: IGraphQLClient, run_id: str) -> DgApiRun:
    """Get run metadata via GraphQL."""
    variables = {"runId": run_id}

    # Try/catch here is a temporary solution until we fix the GQL-- client.execute is throwing an
    # error if the run is not found, instead of returning the error in the response.
    try:
        result = client.execute(RUN_METADATA_QUERY, variables)
    except Exception:
        raise Exception(f"Run not found: {run_id}")

    run_result = result.get("runOrError")
    if not run_result:
        raise Exception(f"Run not found: {run_id}")

    typename = run_result.get("__typename")

    # Handle GraphQL errors
    if run_result.get("__typename") != "Run":
        error_msg = run_result.get("message", f"Graphql error: {typename}")
        raise Exception(error_msg)

    return DgApiRun(
        id=run_result["runId"],
        status=DgApiRunStatus(run_result["status"]),
        created_at=run_result["creationTime"],
        started_at=run_result.get("startTime"),
        ended_at=run_result.get("endTime"),
        job_name=run_result.get("jobName"),
    )
