from dagster._core.utils import check_dagster_package_version

from .asset_defs import build_fivetran_assets, load_assets_from_fivetran_instance
from .ops import fivetran_resync_op, fivetran_sync_op
from .resources import FivetranResource, fivetran_resource
from .types import FivetranOutput
from .version import __version__

try:
    import dagster_managed_elements

    from .managed import FivetranConnector, FivetranDestination, FivetranManagedElementReconciler

except ImportError:
    pass


check_dagster_package_version("dagster-fivetran", __version__)

__all__ = [
    "FivetranResource",
    "fivetran_resource",
    "fivetran_sync_op",
    "fivetran_resync_op",
    "FivetranOutput",
]
