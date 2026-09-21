from collections.abc import Mapping
from typing import Any

from dagster import AssetKey, JobDefinition

OUTPUT_NON_ASSET_SIGIL = "__bigquery_query_metadata_"
BIGQUERY_METADATA_BYTES_BILLED = "__bigquery_bytes_billed"
BIGQUERY_METADATA_SLOTS_MS = "__bigquery_slots_ms"
BIGQUERY_METADATA_JOB_IDS = "__bigquery_job_ids"


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
