"""Core assets and sensors.

This module ties together:
- Kafka ingestion sensors
- Core data assets (raw events, SaaS data, legacy data)
- Resources for Kafka and other integrations
"""

import dagster as dg

from project_multi_workspace_databricks.assets import (
    customer_360_view,
    enriched_customer_profiles,
    hubspot_data,
    legacy_customer_data,
    legacy_transaction_data,
    marketing_attribution,
    order_fulfillment_status,
    process_kafka_events,
    raw_crm_events,
    raw_erp_events,
    salesforce_data,
)
from project_multi_workspace_databricks.sensors import (
    KafkaResource,
    kafka_sensor_factory,
)

# Create Kafka sensors for event ingestion
# In a real deployment, you might have multiple sensors for different topics/partitions
kafka_sensor_erp = kafka_sensor_factory(
    replica_id=0,
    target_asset_key=dg.AssetKey("raw_erp_events"),
)

kafka_sensor_crm = kafka_sensor_factory(
    replica_id=1,
    target_asset_key=dg.AssetKey("raw_crm_events"),
)

# Job for processing Kafka events
kafka_processor_job = dg.define_asset_job(
    name="kafka_processor_job",
    selection=[raw_erp_events, raw_crm_events],
)


@dg.definitions
def core_defs():
    """Define core assets, sensors, and resources."""
    return dg.Definitions(
        assets=[
            # Raw ingestion assets
            raw_erp_events,
            raw_crm_events,
            salesforce_data,
            hubspot_data,
            legacy_customer_data,
            legacy_transaction_data,
            # Transformation assets
            enriched_customer_profiles,
            order_fulfillment_status,
            # Analytics assets
            customer_360_view,
            marketing_attribution,
        ],
        ops=[process_kafka_events],
        sensors=[
            kafka_sensor_erp,
            kafka_sensor_crm,
        ],
        jobs=[
            kafka_processor_job,
        ],
        resources={
            "kafka_resource": KafkaResource(
                bootstrap_servers="localhost:9092",
                group_id="dagster-consumer-group",
                topics=["erp-events", "crm-events"],
            ),
        },
    )
