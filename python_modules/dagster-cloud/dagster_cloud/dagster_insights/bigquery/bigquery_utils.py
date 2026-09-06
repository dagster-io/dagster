from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

from dagster import AssetKey, JobDefinition

OUTPUT_NON_ASSET_SIGIL = "__bigquery_query_metadata_"
BIGQUERY_METADATA_BYTES_BILLED = "__bigquery_bytes_billed"
BIGQUERY_METADATA_SLOTS_MS = "__bigquery_slots_ms"
BIGQUERY_METADATA_JOB_IDS = "__bigquery_job_ids"
INVOCATION_TIME_BUFFER = timedelta(hours=1)


def marker_asset_key_for_job(
    job: JobDefinition,
) -> AssetKey:
    return AssetKey(path=[f"{OUTPUT_NON_ASSET_SIGIL}{job.name}"])


def build_bigquery_cost_metadata(
    job_ids: list[str] | None, bytes_billed: int, slots_ms: int
) -> Mapping[str, Any]:
    metadata: Mapping[str, Any] = {
        BIGQUERY_METADATA_BYTES_BILLED: bytes_billed,
        BIGQUERY_METADATA_SLOTS_MS: slots_ms,
    }
    if job_ids:
        metadata[BIGQUERY_METADATA_JOB_IDS] = job_ids  # ty: ignore[invalid-assignment]
    return metadata


def _parse_run_results_timestamp(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def derive_invocation_time_bounds(run_results_json: Mapping[str, Any]) -> tuple[datetime, datetime]:
    """Return UTC bounds for filtering INFORMATION_SCHEMA.JOBS on creation_time."""
    metadata = run_results_json.get("metadata", {})
    results = run_results_json.get("results", [])

    if metadata.get("invocation_started_at"):
        start = _parse_run_results_timestamp(metadata["invocation_started_at"])
    elif metadata.get("generated_at") and run_results_json.get("elapsed_time") is not None:
        generated_at = _parse_run_results_timestamp(metadata["generated_at"])
        start = generated_at - timedelta(seconds=float(run_results_json["elapsed_time"]))
    else:
        started_at_values = [
            timing["started_at"]
            for result in results
            for timing in result.get("timing", [])
            if timing.get("started_at")
        ]
        if started_at_values:
            start = _parse_run_results_timestamp(min(started_at_values))
        else:
            start = datetime.now(timezone.utc) - timedelta(days=2)

    if metadata.get("generated_at"):
        end = _parse_run_results_timestamp(metadata["generated_at"])
    else:
        completed_at_values = [
            timing["completed_at"]
            for result in results
            for timing in result.get("timing", [])
            if timing.get("completed_at")
        ]
        if completed_at_values:
            end = _parse_run_results_timestamp(max(completed_at_values))
        else:
            end = datetime.now(timezone.utc)

    return start - INVOCATION_TIME_BUFFER, end + INVOCATION_TIME_BUFFER


def format_bigquery_timestamp(value: datetime) -> str:
    utc = value.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%d %H:%M:%S") + f".{utc.microsecond:06d} UTC"
