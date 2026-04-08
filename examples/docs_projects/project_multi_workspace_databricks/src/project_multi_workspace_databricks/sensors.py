"""Kafka sensors for event-based data ingestion.

This module provides sensors that consume events from Kafka topics and trigger
Dagster runs for processing.
"""

import time
from typing import Iterator, Optional

import dagster as dg
from kafka import KafkaConsumer
from pydantic import Field

# Configuration constants
MAX_BATCH_SIZE = 50
TIME_BETWEEN_SENSOR_TICKS = 40  # seconds
MAX_SENSOR_TICK_RUNTIME = 30  # seconds


# start_kafka_resource
class KafkaResource(dg.ConfigurableResource):
    """Resource for connecting to Kafka."""

    bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Comma-separated list of Kafka bootstrap servers",
    )
    group_id: str = Field(
        default="dagster-consumer-group",
        description="Consumer group ID",
    )
    topics: list[str] = Field(
        default_factory=lambda: ["events"],
        description="List of Kafka topics to consume",
    )

    def create_consumer(self) -> KafkaConsumer:
        """Create a Kafka consumer instance."""
        return KafkaConsumer(
            *self.topics,
            bootstrap_servers=self.bootstrap_servers.split(","),
            group_id=self.group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        )


# end_kafka_resource


def kafka_sensor_factory(
    replica_id: int = 0,
    target_asset_key: Optional[dg.AssetKey] = None,
) -> dg.SensorDefinition:
    """Create a Kafka sensor that consumes events and triggers asset materializations.

    Args:
        replica_id: Unique identifier for this sensor instance (for scaling)
        target_asset_key: Asset to materialize when messages are received

    Returns:
        A configured sensor definition
    """

    # start_sensor_body
    @dg.sensor(
        name=f"watch_kafka_replica_{replica_id}",
        minimum_interval_seconds=TIME_BETWEEN_SENSOR_TICKS,
        default_status=dg.DefaultSensorStatus.RUNNING,
    )
    def watch_kafka(
        context: dg.SensorEvaluationContext,
        kafka_resource: KafkaResource,
    ) -> Iterator[dg.RunRequest]:
        """Sensor that polls Kafka for new messages and triggers runs."""
        start_time = time.time()
        consumer = kafka_resource.create_consumer()

        try:
            batch_data: list[dict] = []
            max_offset = -1

            while time.time() - start_time < MAX_SENSOR_TICK_RUNTIME:
                message_batch = consumer.poll(
                    timeout_ms=2000, max_records=MAX_BATCH_SIZE
                )

                if not message_batch:
                    break

                for _topic_partition, messages in message_batch.items():
                    for message in messages:
                        batch_data.append(
                            {
                                "topic": message.topic,
                                "partition": message.partition,
                                "offset": message.offset,
                                "timestamp": message.timestamp,
                                "key": (
                                    message.key.decode("utf-8") if message.key else None
                                ),
                                "value": message.value.decode("utf-8"),
                            }
                        )
                        max_offset = max(max_offset, message.offset)

                if len(batch_data) >= MAX_BATCH_SIZE:
                    break

            if batch_data:
                context.log.info(
                    f"Consumed {len(batch_data)} messages, max_offset={max_offset}"
                )

                yield dg.RunRequest(
                    run_key=f"max_offset_{max_offset}",
                    run_config={
                        "ops": {
                            "process_kafka_events": {
                                "config": {
                                    "batch_data": batch_data,
                                    "max_offset": max_offset,
                                }
                            }
                        }
                    },
                    asset_selection=[target_asset_key] if target_asset_key else None,
                )

                consumer.commit()

        finally:
            consumer.close()

    # end_sensor_body

    return watch_kafka
