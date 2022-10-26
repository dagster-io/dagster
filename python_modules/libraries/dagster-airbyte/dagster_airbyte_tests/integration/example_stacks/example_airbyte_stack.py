import os

from dagster_airbyte import (
    AirbyteConnection,
    AirbyteDestination,
    AirbyteManagedElementReconciler,
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


reconciler = AirbyteManagedElementReconciler(
    airbyte=airbyte_instance,
    connections=[
        local_json_conn,
    ],
    delete_unmentioned_resources=True,
)

# Version with different source

alternate_local_json_source = AirbyteSource(
    name="local-json-input",
    source_type="File",
    source_configuration={
        "url": "/local/different_sample_file.json",
        "format": "json",
        "provider": {"storage": "local"},
        "dataset_name": "my_data_stream",
    },
)


alt_source_local_json_conn = AirbyteConnection(
    name="local-json-conn",
    source=alternate_local_json_source,
    destination=local_json_destination,
    stream_config={
        "my_data_stream": AirbyteSyncMode.FULL_REFRESH_APPEND,
    },
    normalize_data=False,
)

reconciler_different_source = AirbyteManagedElementReconciler(
    airbyte=airbyte_instance,
    connections=[
        alt_source_local_json_conn,
    ],
    delete_unmentioned_resources=True,
)


# Version with different destination

alternate_local_json_destination = AirbyteDestination(
    name="local-json-output",
    destination_type="Local JSON",
    destination_configuration={"destination_path": "/local/different_destination_file.json"},
)


alt_dest_local_json_conn = AirbyteConnection(
    name="local-json-conn",
    source=local_json_source,
    destination=alternate_local_json_destination,
    stream_config={
        "my_data_stream": AirbyteSyncMode.FULL_REFRESH_APPEND,
    },
    normalize_data=False,
)

reconciler_different_dest = AirbyteManagedElementReconciler(
    airbyte=airbyte_instance,
    connections=[
        alt_dest_local_json_conn,
    ],
    delete_unmentioned_resources=True,
)
