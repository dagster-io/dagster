from dagster._core.utils import check_dagster_package_version

try:
    import dagster_managed_elements

    from .managed import (
        AirbyteConnection,
        AirbyteDestination,
        AirbyteDestinationNamespace,
        AirbyteManagedElementReconciler,
        AirbyteSource,
        AirbyteSyncMode,
        load_assets_from_connections,
    )

except ImportError:
    pass

from .asset_defs import (
    build_airbyte_assets,
    load_assets_from_airbyte_instance,
    load_assets_from_airbyte_project,
)
from .ops import airbyte_sync_op
from .resources import AirbyteResource, AirbyteState, airbyte_resource
from .types import AirbyteOutput
from .version import __version__

check_dagster_package_version("dagster-airbyte", __version__)

__all__ = [
    "AirbyteResource",
    "AirbyteOutput",
    "airbyte_resource",
    "airbyte_sync_op",
    "AirbyteState",
]
