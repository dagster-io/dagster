from dagster._core.libraries import DagsterLibraryRegistry

from .asset_decorator import sdf_assets as sdf_assets
from .asset_utils import (
    build_schedule_from_sdf_selection as build_schedule_from_sdf_selection,
    dagster_name_fn as dagster_name_fn,
    default_asset_key_fn as default_asset_key_fn,
)
from .resource import SdfCliResource as SdfCliResource
from .sdf_information_schema import SdfInformationSchema as SdfInformationSchema
from .sdf_workspace import SdfWorkspace as SdfWorkspace
from .version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-sdf", __version__)
