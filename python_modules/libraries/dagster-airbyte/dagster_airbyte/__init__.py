from dagster.core.utils import check_dagster_package_version

from .asset_defs import build_airbyte_assets
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
