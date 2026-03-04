import random

import dagster as dg


@dg.sensor(
    name="kafka_observation_sensor",
    minimum_interval_seconds=60,
    description="Monitors external Kafka stream and emits health observations",
)
def kafka_observation_sensor(context: dg.SensorEvaluationContext):
    messages_per_second = 450 + random.randint(-50, 100)
    consumer_lag_seconds = random.randint(5, 30)
    partition_count = 8
    messages_available = random.randint(5000, 15000)
    stream_health = "healthy" if consumer_lag_seconds < 60 else "degraded"

    context.log.info(
        f"Stream health: {messages_per_second} msg/s, "
        f"{consumer_lag_seconds}s lag, {messages_available} msgs available"
    )

    return dg.SensorResult(
        asset_events=[
            dg.AssetObservation(
                asset_key=dg.AssetKey("streaming_insurance_claims"),
                metadata={
                    "messages_per_second": messages_per_second,
                    "consumer_lag_seconds": consumer_lag_seconds,
                    "partition_count": partition_count,
                    "messages_available": messages_available,
                    "stream_health": stream_health,
                    "kafka_topic": "insurance-claims-v1",
                },
            )
        ]
    )
