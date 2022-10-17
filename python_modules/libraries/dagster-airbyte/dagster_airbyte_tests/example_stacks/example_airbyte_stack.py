import os

from dagster_airbyte import (
    AirbyteConnection,
    AirbyteDestination,
    AirbyteManagedStackReconciler,
    AirbyteSource,
    AirbyteSyncMode,
    airbyte_resource,
)

airbyte_instance = airbyte_resource.configured(
    {
        "host": os.getenv("AIRBYTE_HOSTNAME", "localhost"),
        "port": os.getenv("AIRBYTE_PORT", "80"),
    }
)


local_json_source = AirbyteSource(
    name="local-json-input",
    source_type="File",
    source_configuration={
        "url": "/local/sample_file.json",
        "format": "json",
        "provider": {"storage": "local"},
        "dataset_name": "my_data_stream",
    },
)

local_json_destination = AirbyteDestination(
    name="local-json-output",
    destination_type="Local JSON",
    destination_configuration={"destination_path": "/local/destination_file.json"},
)


local_json_conn = AirbyteConnection(
    name="local-json-conn",
    source=local_json_source,
    destination=local_json_destination,
    stream_config={
        "my_data_stream": AirbyteSyncMode.FULL_REFRESH_APPEND,
    },
    normalize_data=False,
)


reconciler = AirbyteManagedStackReconciler(
    airbyte=airbyte_instance,
    connections=[
        local_json_conn,
    ],
)
