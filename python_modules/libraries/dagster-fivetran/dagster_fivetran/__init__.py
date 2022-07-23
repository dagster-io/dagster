from dagster.core.utils import check_dagster_package_version

from .asset_defs import build_fivetran_assets
from .ops import fivetran_resync_op, fivetran_sync_op
from .resources import FivetranResource, fivetran_resource
from .types import FivetranOutput
from .version import __version__

check_dagster_package_version("dagster-fivetran", __version__)

__all__ = [
    "FivetranResource",
    "fivetran_resource",
    "fivetran_sync_op",
    "fivetran_resync_op",
    "FivetranOutput",
]
