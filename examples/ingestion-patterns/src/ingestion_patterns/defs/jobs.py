from datetime import datetime

import dagster as dg

from ingestion_patterns.defs.poll_kafka_ingestion import poll_kafka_events, process_kafka_events
from ingestion_patterns.defs.pull_api_ingestion import extract_source_data, load_to_storage
from ingestion_patterns.defs.push_webhook_ingestion import process_webhook_data
from ingestion_patterns.resources import WebhookStorageResource

# Jobs
pull_job = dg.define_asset_job(
    name="daily_pull_job",
    selection=[extract_source_data, load_to_storage],
)

poll_job = dg.define_asset_job(
    name="kafka_poll_job",
    selection=[poll_kafka_events, process_kafka_events],
)

webhook_job = dg.define_asset_job(
    name="webhook_processing_job",
    selection=[process_webhook_data],
)

# Schedules
daily_pull_schedule = dg.ScheduleDefinition(
    name="daily_pull_schedule",
    job=pull_job,
    cron_schedule="0 0 * * *",
)


# Sensors
@dg.sensor(job=poll_job, minimum_interval_seconds=60)
def kafka_polling_sensor(context):
    """Sensor that triggers Kafka polling at regular intervals."""
    return dg.RunRequest(
        run_key=f"poll-{int(datetime.now().timestamp())}",
        tags={"source": "kafka", "pattern": "poll"},
    )


@dg.sensor(job=webhook_job, minimum_interval_seconds=10)
def webhook_pending_sensor(
    context: dg.SensorEvaluationContext,
    webhook_storage: WebhookStorageResource,
):
    """Sensor that triggers processing when webhook payloads are pending."""
    storage = webhook_storage.get_all_sources()

    # Check each source for pending payloads
    for source_id, payloads in storage.items():
        if payloads:
            return dg.RunRequest(
                run_key=f"webhook-{source_id}-{int(datetime.now().timestamp())}",
                run_config={"ops": {"process_webhook_data": {"config": {"source_id": source_id}}}},
                tags={"source": source_id, "pattern": "push"},
            )

    return dg.SkipReason("No pending webhook payloads")
