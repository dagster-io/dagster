import os

from dagster_airbyte import (
    AirbyteConnection,
    AirbyteManagedElementReconciler,
    AirbyteSyncMode,
    airbyte_resource,
)
from dagster_airbyte.managed.generated.destinations import PostgresDestination
from dagster_airbyte.managed.generated.sources import PostgresSource

AIRBYTE_CONFIG = {
    "host": "localhost",
    "port": "8000",
    "username": "airbyte",
    "password": os.getenv("AIRBYTE_PASSWORD", "password"),
}

POSTGRES_BASE_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "username": "postgres",
    "password": os.getenv("POSTGRES_PASSWORD", "password"),
    "database": "postgres",
}

airbyte_instance = airbyte_resource.configured(AIRBYTE_CONFIG)

postgres_source = PostgresSource(
    name="postgres_source",
    host=POSTGRES_BASE_CONFIG["host"],
    port=int(POSTGRES_BASE_CONFIG["port"]),
    username=POSTGRES_BASE_CONFIG["username"],
    password=POSTGRES_BASE_CONFIG["password"],
    ssl_mode=PostgresSource.Allow(),
    replication_method=PostgresSource.Standard(),
    tunnel_method=PostgresSource.NoTunnel(),
    database="postgres",
)

postgres_destination = PostgresDestination(
    name="postgres_destinatation",
    host=POSTGRES_BASE_CONFIG["host"],
    port=int(POSTGRES_BASE_CONFIG["port"]),
    username=POSTGRES_BASE_CONFIG["username"],
    password=POSTGRES_BASE_CONFIG["password"],
    schema="public",
    ssl_mode=PostgresDestination.Allow(),
    database="postgres_replica",
)


stream_config = {
    "orders": AirbyteSyncMode.full_refresh_append(),
    "users": AirbyteSyncMode.full_refresh_append(),
}

postgres_to_postgres = AirbyteConnection(
    name="postgres_to_postres",
    source=postgres_source,
    destination=postgres_destination,
    stream_config=stream_config,
    normalize_data=False,
)

airbyte_reconciler = AirbyteManagedElementReconciler(
    airbyte=airbyte_instance,
    connections=[postgres_to_postgres],
)
