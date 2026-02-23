import random

import dagster as dg


@dg.asset(group_name="streaming")
def processed_claims(context: dg.AssetExecutionContext):
    """Downstream asset that processes claims when fresh streaming data is available."""
    context.log.info("Processing fresh claims from stream...")
    return {"records_processed": random.randint(1000, 2000)}


@dg.sensor(
    name="streaming_freshness_sensor",
    minimum_interval_seconds=120,
    description="Triggers downstream processing when fresh streaming data is available",
)
def streaming_freshness_sensor(context: dg.SensorEvaluationContext):
    messages_available = random.randint(500, 2000)
    consumer_lag = random.randint(5, 45)

    context.log.info(f"Checking stream freshness: {messages_available} msgs, {consumer_lag}s lag")

    should_trigger = messages_available > 1000 and consumer_lag < 30

    if should_trigger:
        context.log.info("Fresh data available, triggering downstream processing")
        return dg.SensorResult(
            run_requests=[
                dg.RunRequest(
                    asset_selection=[dg.AssetKey("processed_claims")],
                    tags={
                        "trigger": "fresh_streaming_data",
                        "messages_available": str(messages_available),
                        "consumer_lag_seconds": str(consumer_lag),
                    },
                )
            ]
        )
    else:
        return dg.SensorResult(
            run_requests=[],
            skip_reason=f"Insufficient fresh data: {messages_available} messages, {consumer_lag}s lag",
        )
