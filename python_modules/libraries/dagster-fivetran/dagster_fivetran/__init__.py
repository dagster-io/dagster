from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_fivetran.asset_decorator import fivetran_assets as fivetran_assets
from dagster_fivetran.asset_defs import (
    build_fivetran_assets as build_fivetran_assets,
    build_fivetran_assets_definitions as build_fivetran_assets_definitions,
    load_assets_from_fivetran_instance as load_assets_from_fivetran_instance,
)
from dagster_fivetran.ops import (
    fivetran_resync_op as fivetran_resync_op,
    fivetran_sync_op as fivetran_sync_op,
)
from dagster_fivetran.resources import (
    FivetranResource as FivetranResource,
    FivetranWorkspace as FivetranWorkspace,
    fivetran_resource as fivetran_resource,
    load_fivetran_asset_specs as load_fivetran_asset_specs,
)
from dagster_fivetran.translator import (
    ConnectorSelectorFn as ConnectorSelectorFn,
    DagsterFivetranTranslator as DagsterFivetranTranslator,
    FivetranConnectorTableProps as FivetranConnectorTableProps,
)
from dagster_fivetran.types import FivetranOutput as FivetranOutput
from dagster_fivetran.version import __version__ as __version__

try:
    from dagster_fivetran.managed import (
        FivetranConnector as FivetranConnector,
        FivetranDestination as FivetranDestination,
        FivetranManagedElementReconciler as FivetranManagedElementReconciler,
    )

except ImportError:
    pass


DagsterLibraryRegistry.register("dagster-fivetran", __version__)
