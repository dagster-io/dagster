import dagster as dg
from dagster_duckdb import DuckDBResource

import ingestion_patterns.defs as defs_module
from ingestion_patterns.resources import (
    APIClientResource,
    KafkaConsumerResource,
    WebhookStorageResource,
)


@dg.definitions
def defs():
    return dg.Definitions.merge(
        dg.components.load_defs(defs_module),
        dg.Definitions(
            resources={
                "duckdb": DuckDBResource(database="ingestion_patterns.duckdb"),
                "api_client": APIClientResource(base_url="http://localhost:5051"),
                "kafka_consumer": KafkaConsumerResource(bootstrap_servers="localhost:9094"),
                "webhook_storage": WebhookStorageResource(storage_dir="/tmp/webhook_storage"),
            },
        ),
    )
