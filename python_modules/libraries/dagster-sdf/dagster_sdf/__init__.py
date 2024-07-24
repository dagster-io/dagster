from dagster._core.libraries import DagsterLibraryRegistry

from .asset_decorator import sdf_assets as sdf_assets
from .asset_utils import (
    build_schedule_from_sdf_selection as build_schedule_from_sdf_selection,
    dagster_name_fn as dagster_name_fn,
    default_asset_key_fn as default_asset_key_fn,
)
from .information_schema import SdfInformationSchema as SdfInformationSchema
from .resource import SdfCliResource as SdfCliResource
from .version import __version__ as __version__
from .workspace import SdfWorkspace as SdfWorkspace

DagsterLibraryRegistry.register("dagster-sdf", __version__)
