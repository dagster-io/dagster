from datetime import datetime
from typing import Any

import dagster as dg
import pandas as pd
from dagster_duckdb import DuckDBResource

from ingestion_patterns.resources.mock_apis import clear_webhook_storage, get_webhook_storage


class WebhookPayloadConfig(dg.Config):
    """Configuration for webhook payload processing."""

    source_id: str = "default"
    validate_schema: bool = True


@dg.asset
def process_webhook_data(
    context: dg.AssetExecutionContext,
    config: WebhookPayloadConfig,
    duckdb: DuckDBResource,
) -> dict[str, Any]:
    """Process data received via webhook push and store in DuckDB.

    This asset processes pending webhook payloads from storage,
    validates them, ensures idempotency, and stores in DuckDB.
    """
    # Get webhook storage (in production, this would be a proper queue/database)
    webhook_storage = get_webhook_storage()

    # Retrieve pending payloads for this source
    pending = webhook_storage.get(config.source_id, [])

    if not pending:
        context.log.info(f"No pending payloads for source: {config.source_id}")
        return {"processed": [], "count": 0, "duplicates": 0}

    context.log.info(f"Processing {len(pending)} pending payloads from {config.source_id}")

    processed = []
    duplicates = 0
    invalid = 0

    # Track processed IDs for idempotency
    seen_ids: set[str] = set()

    for payload in pending:
        # Validate required fields
        if config.validate_schema:
            if not _validate_payload_schema(payload):
                context.log.warning(f"Invalid payload schema: {payload.get('id', 'unknown')}")
                invalid += 1
                continue

        # Idempotency check: skip if we've already processed this ID
        payload_id = payload.get("id")
        if payload_id is None:
            context.log.warning("Payload missing ID field")
            invalid += 1
            continue

        if payload_id in seen_ids:
            context.log.warning(f"Duplicate payload ID: {payload_id}")
            duplicates += 1
            continue

        seen_ids.add(str(payload_id))

        # Process the payload
        processed_item = {
            "id": payload_id,
            "source": config.source_id,
            "timestamp": payload.get("timestamp"),
            "data": str(payload.get("data", {})),  # Convert dict to string for DuckDB
            "processed_at": datetime.now().isoformat(),
            "run_id": context.run.run_id,
        }

        processed.append(processed_item)

    # Clear processed payloads from storage
    clear_webhook_storage(config.source_id)

    # Store processed payloads in DuckDB
    total_count = 0
    if processed:
        webhook_df = pd.DataFrame(processed)
        with duckdb.get_connection() as conn:
            conn.execute("CREATE SCHEMA IF NOT EXISTS ingestion")
            # Register DataFrame and create table
            conn.register("webhook_df", webhook_df)
            conn.execute(
                "CREATE TABLE IF NOT EXISTS ingestion.webhook_data AS SELECT * FROM webhook_df WHERE 1=0"
            )
            conn.execute("INSERT INTO ingestion.webhook_data SELECT * FROM webhook_df")

            result = conn.execute("SELECT COUNT(*) FROM ingestion.webhook_data").fetchone()
            total_count = result[0] if result else 0
        context.log.info(f"Stored {len(processed)} payloads in ingestion.webhook_data")

    context.log.info(
        f"Processed {len(processed)} payloads, {duplicates} duplicates, {invalid} invalid"
    )

    context.add_output_metadata(
        {
            "processed_count": len(processed),
            "total_in_storage": total_count,
            "duplicates": duplicates,
            "invalid": invalid,
        }
    )

    return {
        "processed": processed,
        "count": len(processed),
        "duplicates": duplicates,
        "invalid": invalid,
    }


def _validate_payload_schema(payload: dict[str, Any]) -> bool:
    """Validate that payload has required schema fields."""
    required_fields = ["id", "timestamp", "data"]
    return all(field in payload for field in required_fields)
