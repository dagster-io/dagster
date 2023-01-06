from dagster._core.utils import check_dagster_package_version

try:
    import dagster_managed_elements  # noqa: F401

    from .managed import (
        AirbyteConnection as AirbyteConnection,
        AirbyteDestination as AirbyteDestination,
        AirbyteDestinationNamespace as AirbyteDestinationNamespace,
        AirbyteManagedElementReconciler as AirbyteManagedElementReconciler,
        AirbyteSource as AirbyteSource,
        AirbyteSyncMode as AirbyteSyncMode,
        load_assets_from_connections as load_assets_from_connections,
    )

except ImportError:
    pass

from .asset_defs import (
    build_airbyte_assets as build_airbyte_assets,
    load_assets_from_airbyte_instance as load_assets_from_airbyte_instance,
    load_assets_from_airbyte_project as load_assets_from_airbyte_project,
)
from .ops import airbyte_sync_op as airbyte_sync_op
from .resources import (
    AirbyteResource as AirbyteResource,
    AirbyteState as AirbyteState,
    airbyte_resource as airbyte_resource,
)
from .types import AirbyteOutput as AirbyteOutput
from .version import __version__ as __version__

check_dagster_package_version("dagster-airbyte", __version__)
