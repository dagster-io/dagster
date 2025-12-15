import json
from datetime import datetime
from typing import Any

import dagster as dg
import pandas as pd
from dagster._core.events import StepMaterializationData
from dagster_duckdb import DuckDBResource

from ingestion_patterns.resources.mock_apis import MockKafkaConsumer


def _create_kafka_consumer(
    topic: str,
    consumer_group: str,
    bootstrap_servers: str | None,
):
    """Create a Kafka consumer - either mock or real based on bootstrap_servers.

    Args:
        topic: Kafka topic to consume from
        consumer_group: Consumer group ID
        bootstrap_servers: Kafka bootstrap servers. If None or empty, uses mock.

    Returns:
        A consumer instance (mock or real confluent-kafka Consumer)
    """
    if not bootstrap_servers:
        # Use mock consumer for testing/demo
        return MockKafkaConsumer(topic, consumer_group)

    # Use real Kafka consumer
    # Lazy import to avoid requiring confluent-kafka for mock usage
    try:
        from confluent_kafka import Consumer
    except ImportError as e:
        raise ImportError(
            "confluent-kafka is required for real Kafka connections. "
            "Install with: pip install 'ingestion-patterns[kafka]'"
        ) from e

    return Consumer(
        {
            "bootstrap.servers": bootstrap_servers,
            "group.id": consumer_group,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )


class PollingConfig(dg.Config):
    """Configuration for polling-based ingestion."""

    kafka_topic: str = "transactions"
    consumer_group: str = "dagster-ingestion"
    poll_interval_seconds: int = 60
    max_records_per_poll: int = 100
    # Set to Kafka bootstrap servers (e.g., "localhost:9094") for real Kafka
    # Leave empty to use mock consumer
    bootstrap_servers: str = ""


@dg.asset
def poll_kafka_events(
    context: dg.AssetExecutionContext,
    config: PollingConfig,
) -> dict[str, Any]:
    """Poll Kafka topic for new events since last checkpoint.

    This asset maintains state (last processed offset) and only processes
    new messages, ensuring idempotency and efficiency.

    Configure bootstrap_servers to connect to real Kafka, or leave empty for mock.
    """
    using_real_kafka = bool(config.bootstrap_servers)

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

    context.log.info(
        f"Polling from offset {start_offset} ({'real Kafka' if using_real_kafka else 'mock'})"
    )

    # Create consumer (mock or real based on config)
    consumer = _create_kafka_consumer(
        config.kafka_topic,
        config.consumer_group,
        config.bootstrap_servers if using_real_kafka else None,
    )

    # Poll for messages
    if using_real_kafka:
        messages = _poll_real_kafka(
            consumer,
            config.kafka_topic,
            config.poll_interval_seconds,
            config.max_records_per_poll,
            context,
        )
    else:
        # Mock consumer
        consumer.seek(start_offset)
        messages = consumer.poll(
            timeout_ms=config.poll_interval_seconds * 1000,
            max_records=config.max_records_per_poll,
        )
        consumer.close()

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
            "using_real_kafka": using_real_kafka,
        }
    )

    return {
        "messages": parsed_messages,
        "last_offset": last_processed_offset,
        "count": len(parsed_messages),
    }


def _poll_real_kafka(
    consumer,
    topic: str,
    timeout_seconds: int,
    max_records: int,
    context: dg.AssetExecutionContext,
) -> list[dict[str, Any]]:
    """Poll messages from real Kafka using confluent-kafka Consumer."""
    consumer.subscribe([topic])

    messages = []
    deadline = datetime.now().timestamp() + timeout_seconds

    while len(messages) < max_records:
        remaining_time = deadline - datetime.now().timestamp()
        if remaining_time <= 0:
            break

        msg = consumer.poll(timeout=min(remaining_time, 1.0))

        if msg is None:
            continue

        if msg.error():
            context.log.warning(f"Kafka error: {msg.error()}")
            continue

        messages.append(
            {
                "offset": msg.offset(),
                "partition": msg.partition(),
                "timestamp": msg.timestamp()[1] if msg.timestamp() else 0,
                "key": msg.key().decode("utf-8") if msg.key() else None,
                "value": msg.value().decode("utf-8") if msg.value() else "{}",
            }
        )

    # Commit offsets after successful processing
    if messages:
        consumer.commit()

    consumer.close()
    return messages


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
            # Register DataFrame and create table
            conn.register("events_df", events_df)
            conn.execute(
                "CREATE TABLE IF NOT EXISTS ingestion.kafka_events AS SELECT * FROM events_df WHERE 1=0"
            )
            conn.execute("INSERT INTO ingestion.kafka_events SELECT * FROM events_df")

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
