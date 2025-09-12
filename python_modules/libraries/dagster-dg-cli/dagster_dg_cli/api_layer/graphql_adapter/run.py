"""GraphQL implementation for run operations."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.run import RunList

# GraphQL queries
LIST_RUNS_QUERY = """
query ListRuns($cursor: String, $limit: Int, $filter: RunsFilter) {
    runsOrError(cursor: $cursor, limit: $limit, filter: $filter) {
        ... on Runs {
            results {
                id
                runId
                status
                jobName
                pipelineName
                startTime
                endTime
                updateTime
                creationTime
                canTerminate
            }
            count
        }
        ... on InvalidPipelineRunsFilterError {
            message
        }
        ... on PythonError {
            message
        }
    }
}
"""


def process_runs_response(graphql_response: dict[str, Any]) -> "RunList":
    """Process GraphQL response into RunList.

    This is a pure function that can be easily tested without mocking GraphQL clients.

    Args:
        graphql_response: Raw GraphQL response containing "runsOrError"

    Returns:
        RunList: Processed runs data

    Raises:
        Exception: If GraphQL response contains errors
    """
    # Import pydantic models only when needed
    from dagster_dg_cli.api_layer.schemas.run import Run, RunList, RunStatus

    runs_or_error = graphql_response.get("runsOrError")

    if not runs_or_error:
        raise Exception("Invalid GraphQL response: missing runsOrError")

    # Check for GraphQL errors
    if "message" in runs_or_error:
        raise Exception(f"GraphQL error: {runs_or_error['message']}")

    results = runs_or_error.get("results", [])
    count = runs_or_error.get("count", 0)

    runs = []
    for r in results:
        # Convert timestamp fields from GraphQL (float seconds since epoch) to datetime
        start_time = None
        if r.get("startTime"):
            start_time = datetime.fromtimestamp(r["startTime"])

        end_time = None
        if r.get("endTime"):
            end_time = datetime.fromtimestamp(r["endTime"])

        update_time = None
        if r.get("updateTime"):
            update_time = datetime.fromtimestamp(r["updateTime"])

        creation_time = datetime.fromtimestamp(r["creationTime"])

        run = Run(
            id=r["id"],
            run_id=r["runId"],
            status=RunStatus[r["status"]],
            job_name=r["jobName"],
            pipeline_name=r.get("pipelineName"),
            start_time=start_time,
            end_time=end_time,
            update_time=update_time,
            creation_time=creation_time,
            can_terminate=r.get("canTerminate", False),
        )
        runs.append(run)

    return RunList(
        items=runs,
        total=count,
        has_next_page=False,  # Simple implementation - no pagination for now
    )


def list_runs_via_graphql(
    client: IGraphQLClient,
    limit: Optional[int] = None,
    status: Optional[str] = None,
    job_name: Optional[str] = None,
    cursor: Optional[str] = None,
) -> "RunList":
    """Fetch runs using GraphQL.

    Args:
        client: GraphQL client instance
        limit: Maximum number of runs to return
        status: Filter by run status (e.g., "SUCCESS", "FAILURE")
        job_name: Filter by job name
        cursor: Pagination cursor for next page

    Returns:
        RunList: List of runs matching the filters
    """
    variables = {}

    if cursor:
        variables["cursor"] = cursor

    if limit:
        variables["limit"] = limit

    # Build filter object
    run_filter = {}
    if status:
        run_filter["statuses"] = [status]
    if job_name:
        run_filter["pipelineName"] = job_name  # GraphQL uses pipelineName for job filtering

    if run_filter:
        variables["filter"] = run_filter

    result = client.execute(LIST_RUNS_QUERY, variables)
    return process_runs_response(result)
