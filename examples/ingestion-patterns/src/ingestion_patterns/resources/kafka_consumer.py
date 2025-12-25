from datetime import datetime
from typing import Any

import dagster as dg


class KafkaConsumerResource(dg.ConfigurableResource):
    """Resource for consuming messages from Kafka.

    This resource connects to a real Kafka cluster.
    For testing, override this resource with a mock implementation.
    """

    bootstrap_servers: str = "localhost:9094"
    consumer_group: str = "dagster-ingestion"
    auto_offset_reset: str = "earliest"

    def poll_messages(
        self,
        topic: str,
        timeout_seconds: int = 60,
        max_records: int = 100,
        context: dg.AssetExecutionContext | None = None,
    ) -> list[dict[str, Any]]:
        """Poll messages from a Kafka topic.

        Args:
            topic: The Kafka topic to consume from
            timeout_seconds: Maximum time to wait for messages
            max_records: Maximum number of records to return
            context: Optional asset execution context for logging

        Returns:
            List of message dictionaries with offset, partition, timestamp, key, value
        """
        try:
            from confluent_kafka import Consumer
        except ImportError as e:
            raise ImportError(
                "confluent-kafka is required for Kafka connections. "
                "Install with: pip install 'ingestion-patterns[kafka]'"
            ) from e

        consumer = Consumer(
            {
                "bootstrap.servers": self.bootstrap_servers,
                "group.id": self.consumer_group,
                "auto.offset.reset": self.auto_offset_reset,
                "enable.auto.commit": False,
            }
        )

        consumer.subscribe([topic])

        messages = []
        deadline = datetime.now().timestamp() + timeout_seconds

        try:
            while len(messages) < max_records:
                remaining_time = deadline - datetime.now().timestamp()
                if remaining_time <= 0:
                    break

                msg = consumer.poll(timeout=min(remaining_time, 1.0))

                if msg is None:
                    continue

                if msg.error():
                    if context:
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
        finally:
            consumer.close()

        return messages
