from dagster._core.libraries import DagsterLibraryRegistry

from .asset_defs import (
    build_fivetran_assets as build_fivetran_assets,
    load_assets_from_fivetran_instance as load_assets_from_fivetran_instance,
)
from .ops import (
    fivetran_resync_op as fivetran_resync_op,
    fivetran_sync_op as fivetran_sync_op,
)
from .resources import (
    FivetranResource as FivetranResource,
    fivetran_resource as fivetran_resource,
)
from .types import FivetranOutput as FivetranOutput
from .version import __version__ as __version__

try:
    from .managed import (
        FivetranConnector as FivetranConnector,
        FivetranDestination as FivetranDestination,
        FivetranManagedElementReconciler as FivetranManagedElementReconciler,
    )

except ImportError:
    pass


DagsterLibraryRegistry.register("dagster-fivetran", __version__)
