import json
from datetime import datetime
from typing import Any

import dagster as dg
import pandas as pd
from dagster._core.events import StepMaterializationData
from dagster_duckdb import DuckDBResource

from ingestion_patterns.resources import KafkaConsumerResource


class PollingConfig(dg.Config):
    """Configuration for polling-based ingestion."""

    kafka_topic: str = "transactions"
    poll_interval_seconds: int = 60
    max_records_per_poll: int = 100


@dg.asset
def poll_kafka_events(
    context: dg.AssetExecutionContext,
    config: PollingConfig,
    kafka_consumer: KafkaConsumerResource,
) -> dict[str, Any]:
    """Poll Kafka topic for new events since last checkpoint.

    This asset maintains state (last processed offset) and only processes
    new messages, ensuring idempotency and efficiency.
    """
    # Load last processed offset from previous materialization
    last_event = context.instance.get_latest_materialization_event(context.asset_key)

    start_offset = 0
    if last_event and last_event.dagster_event:
        # Extract offset from last materialization metadata
        mat_data = last_event.dagster_event.event_specific_data
        if isinstance(mat_data, StepMaterializationData):
            metadata = mat_data.materialization.metadata
            if "last_offset" in metadata:
                offset_value = metadata["last_offset"].value
                start_offset = int(str(offset_value)) + 1

    context.log.info(f"Polling from offset {start_offset}")

    # Poll for messages using the resource
    messages = kafka_consumer.poll_messages(
        topic=config.kafka_topic,
        timeout_seconds=config.poll_interval_seconds,
        max_records=config.max_records_per_poll,
        context=context,
    )

    if not messages:
        context.log.info("No new messages")
        return {
            "messages": [],
            "last_offset": start_offset - 1,
            "count": 0,
        }

    # Parse and validate messages
    parsed_messages = []
    seen_event_ids: set[str] = set()  # For idempotency

    for msg in messages:
        # Exception handling acceptable here: json.loads API uses exceptions for
        # invalid JSON (no way to LBYL check JSON validity without parsing)
        try:
            value = json.loads(msg["value"])
        except json.JSONDecodeError as e:
            context.log.warning(f"Failed to parse message at offset {msg['offset']}: {e}")
            continue

        event_id = value.get("event_id")

        # Idempotency check: skip if we've seen this event ID
        if event_id in seen_event_ids:
            context.log.warning(f"Duplicate event ID: {event_id}")
            continue

        seen_event_ids.add(event_id)

        parsed_messages.append(
            {
                "offset": msg["offset"],
                "partition": msg["partition"],
                "event_id": event_id,
                "event_type": value.get("event_type"),
                "data": value,
                "kafka_timestamp": msg["timestamp"],
            }
        )

    last_processed_offset = messages[-1]["offset"]

    context.log.info(
        f"Processed {len(parsed_messages)} messages, last offset: {last_processed_offset}"
    )

    # Store metadata for next run
    context.add_output_metadata(
        {
            "message_count": len(parsed_messages),
            "last_offset": last_processed_offset,
            "start_offset": start_offset,
            "poll_timestamp": datetime.now().isoformat(),
        }
    )

    return {
        "messages": parsed_messages,
        "last_offset": last_processed_offset,
        "count": len(parsed_messages),
    }


@dg.asset
def process_kafka_events(
    context: dg.AssetExecutionContext,
    poll_kafka_events: dict[str, Any],
    duckdb: DuckDBResource,
) -> dict[str, Any]:
    """Process polled Kafka events and store in DuckDB.

    This asset takes the polled messages and processes them,
    applying business logic and validation, then stores in DuckDB.
    """
    messages = poll_kafka_events.get("messages", [])

    if not messages:
        context.log.info("No messages to process")
        return {"processed": [], "count": 0}

    processed = []
    errors = []

    for msg in messages:
        # LBYL: Validate required fields exist before processing
        if "data" not in msg:
            context.log.error(f"Event {msg.get('event_id')} missing 'data' field")
            errors.append(
                {
                    "event_id": msg.get("event_id"),
                    "error": "Missing 'data' field",
                    "offset": msg.get("offset"),
                }
            )
            continue

        event_data = msg["data"]

        # LBYL: Validate transaction amount before processing
        amount = event_data.get("amount", 0)
        if amount < 0:
            context.log.error(f"Event {msg.get('event_id')} has invalid amount: {amount}")
            errors.append(
                {
                    "event_id": msg.get("event_id"),
                    "error": f"Invalid amount: {amount}",
                    "offset": msg.get("offset"),
                }
            )
            continue

        processed_item = {
            "event_id": msg["event_id"],
            "event_type": msg["event_type"],
            "amount": amount,
            "processed_at": datetime.now().isoformat(),
            "kafka_offset": msg["offset"],
        }

        processed.append(processed_item)

    # Store processed events in DuckDB
    if processed:
        events_df = pd.DataFrame(processed)
        with duckdb.get_connection() as conn:
            conn.execute("CREATE SCHEMA IF NOT EXISTS ingestion")
            conn.register("events_df", events_df)
            # Check if table exists
            table_exists = conn.execute(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='ingestion' AND table_name='kafka_events'"
            ).fetchone()
            if table_exists:
                conn.execute("INSERT INTO ingestion.kafka_events SELECT * FROM events_df")
            else:
                conn.execute("CREATE TABLE ingestion.kafka_events AS SELECT * FROM events_df")

            result = conn.execute("SELECT COUNT(*) FROM ingestion.kafka_events").fetchone()
            total_count = result[0] if result else 0
        context.log.info(f"Stored {len(processed)} events in ingestion.kafka_events")
    else:
        total_count = 0

    context.log.info(f"Processed {len(processed)} events, {len(errors)} errors")

    context.add_output_metadata(
        {
            "processed_count": len(processed),
            "total_in_storage": total_count,
            "error_count": len(errors),
            "errors": errors if errors else None,
        }
    )

    return {
        "processed": processed,
        "count": len(processed),
        "errors": errors,
    }
