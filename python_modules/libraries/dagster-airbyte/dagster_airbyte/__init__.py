from dagster._core.libraries import DagsterLibraryRegistry

try:
    from .managed import (
        AirbyteSource as AirbyteSource,
        AirbyteSyncMode as AirbyteSyncMode,
        AirbyteConnection as AirbyteConnection,
        AirbyteDestination as AirbyteDestination,
        AirbyteDestinationNamespace as AirbyteDestinationNamespace,
        AirbyteManagedElementReconciler as AirbyteManagedElementReconciler,
        load_assets_from_connections as load_assets_from_connections,
    )

except ImportError:
    pass

from .ops import airbyte_sync_op as airbyte_sync_op
from .types import AirbyteOutput as AirbyteOutput
from .version import __version__ as __version__
from .resources import (
    AirbyteState as AirbyteState,
    AirbyteResource as AirbyteResource,
    AirbyteCloudResource as AirbyteCloudResource,
    airbyte_resource as airbyte_resource,
    airbyte_cloud_resource as airbyte_cloud_resource,
)
from .asset_defs import (
    build_airbyte_assets as build_airbyte_assets,
    load_assets_from_airbyte_project as load_assets_from_airbyte_project,
    load_assets_from_airbyte_instance as load_assets_from_airbyte_instance,
)

DagsterLibraryRegistry.register("dagster-airbyte", __version__)
