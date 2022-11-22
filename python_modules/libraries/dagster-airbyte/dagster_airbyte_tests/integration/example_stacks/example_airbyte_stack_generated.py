import os

from dagster_airbyte import (
    AirbyteConnection,
    AirbyteManagedElementReconciler,
    AirbyteSyncMode,
    airbyte_resource,
)
from dagster_airbyte.managed.generated.destinations import LocalJsonDestination
from dagster_airbyte.managed.generated.sources import FileSource

airbyte_instance = airbyte_resource.configured(
    {
        "host": os.getenv("AIRBYTE_HOSTNAME", "localhost"),
        "port": os.getenv("AIRBYTE_PORT", "80"),
    }
)


local_json_conn = AirbyteConnection(
    name="local-json-conn",
    source=FileSource(
        name="local-json-input",
        dataset_name="my_data_stream",
        format="json",
        url="/local/sample_file.json",
        provider=FileSource.LocalFilesystemLimited(),
    ),
    destination=LocalJsonDestination(
        name="local-json-output",
        destination_path="/local/destination_file.json",
    ),
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
