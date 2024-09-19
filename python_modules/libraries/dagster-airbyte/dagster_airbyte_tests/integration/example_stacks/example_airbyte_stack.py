import os

from dagster_airbyte import (
    AirbyteConnection,
    AirbyteDestination,
    AirbyteDestinationNamespace,
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
        "my_data_stream": AirbyteSyncMode.full_refresh_append(),
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
        "my_data_stream": AirbyteSyncMode.full_refresh_append(),
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
        "my_data_stream": AirbyteSyncMode.full_refresh_append(),
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


# Version with different destination type, same name

local_csv_destination = AirbyteDestination(
    name="local-json-output",
    destination_type="Local CSV",
    destination_configuration={"destination_path": "/local/destination_file.csv"},
)


local_csv_conn = AirbyteConnection(
    name="local-json-conn",
    source=local_json_source,
    destination=local_csv_destination,
    stream_config={
        "my_data_stream": AirbyteSyncMode.full_refresh_append(),
    },
    normalize_data=False,
)

reconciler_csv = AirbyteManagedElementReconciler(
    airbyte=airbyte_instance,
    connections=[
        local_csv_conn,
    ],
    delete_unmentioned_resources=True,
)

# Version with destination namespace as destination default


dest_default_local_json_conn = AirbyteConnection(
    name="local-json-conn",
    source=local_json_source,
    destination=local_json_destination,
    stream_config={
        "my_data_stream": AirbyteSyncMode.full_refresh_append(),
    },
    normalize_data=False,
    destination_namespace=AirbyteDestinationNamespace.DESTINATION_DEFAULT,
)


reconciler_dest_default = AirbyteManagedElementReconciler(
    airbyte=airbyte_instance,
    connections=[
        dest_default_local_json_conn,
    ],
    delete_unmentioned_resources=True,
)

# Version with destination namespace as custom

custom_namespace_local_json_conn = AirbyteConnection(
    name="local-json-conn",
    source=local_json_source,
    destination=local_json_destination,
    stream_config={
        "my_data_stream": AirbyteSyncMode.full_refresh_append(),
    },
    normalize_data=False,
    destination_namespace="my-cool-namespace",
)


reconciler_custom_namespace = AirbyteManagedElementReconciler(
    airbyte=airbyte_instance,
    connections=[
        custom_namespace_local_json_conn,
    ],
    delete_unmentioned_resources=True,
)


# Version with different sync mode


alt_sync_mode_local_json_conn = AirbyteConnection(
    name="local-json-conn",
    source=local_json_source,
    destination=local_json_destination,
    stream_config={
        "my_data_stream": AirbyteSyncMode.incremental_append(cursor_field="foo"),
    },
    normalize_data=False,
)

reconciler_alt_sync_mode = AirbyteManagedElementReconciler(
    airbyte=airbyte_instance,
    connections=[
        alt_sync_mode_local_json_conn,
    ],
    delete_unmentioned_resources=True,
)


# Version with custom prefix

custom_prefix_local_json_conn = AirbyteConnection(
    name="local-json-conn",
    source=local_json_source,
    destination=local_json_destination,
    stream_config={
        "my_data_stream": AirbyteSyncMode.full_refresh_append(),
    },
    normalize_data=False,
    prefix="my_prefix",
)


reconciler_custom_prefix = AirbyteManagedElementReconciler(
    airbyte=airbyte_instance,
    connections=[
        custom_prefix_local_json_conn,
    ],
    delete_unmentioned_resources=True,
)
