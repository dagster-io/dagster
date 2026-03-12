"""GraphQL adapter for run metadata."""

from typing import Any

from dagster_dg_cli.api_layer.schemas.run import DgApiRun, DgApiRunList, DgApiRunStatus
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


LIST_RUNS_QUERY = """
query DgApiListRunsQuery($filter: RunsFilter, $cursor: String, $limit: Int) {
    runsOrError(filter: $filter, cursor: $cursor, limit: $limit) {
        __typename
        ... on Runs {
            results {
                runId
                status
                creationTime
                startTime
                endTime
                jobName
            }
        }
        ... on PythonError {
            message
            stack
        }
    }
}
"""


def process_runs_response(graphql_response: dict[str, Any]) -> DgApiRunList:
    """Process GraphQL response into DgApiRunList.

    This is a pure function that can be easily tested without mocking GraphQL clients.
    """
    runs_or_error = graphql_response.get("runsOrError", {})
    typename = runs_or_error.get("__typename")

    if typename == "PythonError":
        error_msg = runs_or_error.get("message", "Unknown GraphQL error")
        raise Exception(f"GraphQL error: {error_msg}")

    if typename != "Runs":
        raise Exception(f"Unexpected response type: {typename}")

    results = runs_or_error.get("results", [])

    runs = [
        DgApiRun(
            id=r["runId"],
            status=DgApiRunStatus(r["status"]),
            created_at=r["creationTime"],
            started_at=r.get("startTime"),
            ended_at=r.get("endTime"),
            job_name=r.get("jobName"),
        )
        for r in results
    ]

    return DgApiRunList(items=runs)


def list_runs_via_graphql(
    client: IGraphQLClient,
    limit: int = 50,
    cursor: str | None = None,
    statuses: tuple[str, ...] = (),
    job_name: str | None = None,
) -> DgApiRunList:
    """Fetch runs using GraphQL with optional filtering."""
    variables: dict[str, Any] = {"limit": limit}

    if cursor:
        variables["cursor"] = cursor

    run_filter: dict[str, Any] = {}
    if statuses:
        run_filter["statuses"] = list(statuses)
    if job_name:
        run_filter["pipelineName"] = job_name

    if run_filter:
        variables["filter"] = run_filter

    result = client.execute(LIST_RUNS_QUERY, variables)
    return process_runs_response(result)
