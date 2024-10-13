from dagster._core.libraries import DagsterLibraryRegistry

from dagster_sdf.asset_decorator import sdf_assets as sdf_assets
from dagster_sdf.asset_utils import (
    build_schedule_from_sdf_selection as build_schedule_from_sdf_selection,
    dagster_name_fn as dagster_name_fn,
    default_asset_key_fn as default_asset_key_fn,
)
from dagster_sdf.resource import SdfCliResource as SdfCliResource
from dagster_sdf.sdf_information_schema import SdfInformationSchema as SdfInformationSchema
from dagster_sdf.sdf_workspace import SdfWorkspace as SdfWorkspace
from dagster_sdf.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-sdf", __version__)
