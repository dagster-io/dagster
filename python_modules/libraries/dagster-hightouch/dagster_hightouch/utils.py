from typing import Type

from dateutil import parser

from .types import SyncRunParsedOutput


def parse_sync_run_details(sync_run_details) -> Type[SyncRunParsedOutput]:
    x = SyncRunParsedOutput

    x.created_at = None
    x.started_at = None
    x.finished_at = None
    x.elapsed_seconds = None

    if sync_run_details.get("createdAt"):
        x.created_at = parser.parse(sync_run_details["createdAt"])
    if sync_run_details.get("startedAt"):
        x.started_at = parser.parse(sync_run_details["startedAt"])
    if sync_run_details.get("finishedAt"):
        x.finished_at = parser.parse(sync_run_details["finishedAt"])

    if x.finished_at and x.started_at:
        x.elapsed_seconds = (x.finished_at - x.started_at).seconds

    x.planned_add = sync_run_details["plannedRows"].get("addedCount")
    x.planned_change = sync_run_details["plannedRows"].get("changedCount")
    x.planned_remove = sync_run_details["plannedRows"].get("removedCount")

    x.successful_add = sync_run_details["successfulRows"].get("addedCount")
    x.successful_change = sync_run_details["successfulRows"].get("changedCount")
    x.successful_remove = sync_run_details["successfulRows"].get("removedCount")

    x.failed_add = sync_run_details["failedRows"].get("addedCount")
    x.failed_change = sync_run_details["failedRows"].get("changedCount")
    x.failed_remove = sync_run_details["failedRows"].get("removedCount")

    x.query_size = sync_run_details.get("querySize")
    x.status = sync_run_details.get("status")
    x.completion_ratio = float(sync_run_details.get("completionRatio", 0))
    x.error = sync_run_details.get("error")

    return x


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
