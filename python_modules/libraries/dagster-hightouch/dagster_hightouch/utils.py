from dateutil import parser

from dagster_hightouch.types import SyncRunParsedOutput


def parse_sync_run_details(sync_run_details) -> SyncRunParsedOutput:
    created_at = None
    started_at = None
    finished_at = None
    elapsed_seconds = None

    if sync_run_details.get("createdAt"):
        created_at = parser.parse(sync_run_details["createdAt"])
    if sync_run_details.get("startedAt"):
        started_at = parser.parse(sync_run_details["startedAt"])
    if sync_run_details.get("finishedAt"):
        finished_at = parser.parse(sync_run_details["finishedAt"])

    if finished_at and started_at:
        elapsed_seconds = (finished_at - started_at).seconds

    planned_add = sync_run_details["plannedRows"].get("addedCount")
    planned_change = sync_run_details["plannedRows"].get("changedCount")
    planned_remove = sync_run_details["plannedRows"].get("removedCount")

    successful_add = sync_run_details["successfulRows"].get("addedCount")
    successful_change = sync_run_details["successfulRows"].get("changedCount")
    successful_remove = sync_run_details["successfulRows"].get("removedCount")

    failed_add = sync_run_details["failedRows"].get("addedCount")
    failed_change = sync_run_details["failedRows"].get("changedCount")
    failed_remove = sync_run_details["failedRows"].get("removedCount")

    query_size = sync_run_details.get("querySize")
    status = sync_run_details.get("status")
    completion_ratio = float(sync_run_details.get("completionRatio", 0))
    error = sync_run_details.get("error")

    return SyncRunParsedOutput(
        created_at=created_at,
        started_at=started_at,
        finished_at=finished_at,
        elapsed_seconds=elapsed_seconds,
        planned_add=planned_add,
        planned_change=planned_change,
        planned_remove=planned_remove,
        successful_add=successful_add,
        successful_change=successful_change,
        successful_remove=successful_remove,
        failed_add=failed_add,
        failed_change=failed_change,
        failed_remove=failed_remove,
        query_size=query_size,
        status=status,
        completion_ratio=completion_ratio,
        error=error,
    )


def generate_metadata_from_parsed_run(parsed_output: SyncRunParsedOutput):
    return {
        "elapsed_seconds": parsed_output.elapsed_seconds or 0,
        "planned_add": parsed_output.planned_add,
        "planned_change": parsed_output.planned_change,
        "planned_remove": parsed_output.planned_remove,
        "successful_add": parsed_output.successful_add,
        "successful_change": parsed_output.successful_change,
        "successful_remove": parsed_output.successful_remove,
        "failed_add": parsed_output.failed_add,
        "failed_change": parsed_output.failed_change,
        "failed_remove": parsed_output.failed_remove,
        "query_size": parsed_output.query_size,
    }
