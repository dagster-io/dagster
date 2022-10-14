from abc import abstractmethod
import os
from typing import Optional, Set
from dagster import build_init_resource_context, repository, with_resources
from dagster._core.definitions.resource_requirement import ResourceAddable
from dagster_airbyte import (
    airbyte_resource,
    load_assets_from_airbyte_instance,
    load_assets_from_airbyte_project,
    AirbyteSyncMode,
    AirbyteSource,
    AirbyteDestination,
    AirbyteConnection,
)

from dagster_airbyte.managed import AirbyteManagedStackReconciler


airbyte_instance = airbyte_resource.configured(
    {
        "host": os.getenv("AIRBYTE_HOSTNAME", "localhost2"),
        "port": "8000",
    }
)

# pokeapi_source = AirbyteSource(
#     name="pokeapi-source",
#     source_type="PokeAPI",
#     source_configuration={
#         "pokemon_name": "snorlax",
#     },
# )


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
    destination_configuration={"destination_path": "./d"},
)


pokeapi_to_local_json_conn = AirbyteConnection(
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
        pokeapi_to_local_json_conn,
    ],
)
