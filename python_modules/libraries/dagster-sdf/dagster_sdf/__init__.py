from dagster._core.libraries import DagsterLibraryRegistry

from .asset_decorator import sdf_assets as sdf_assets
from .information_schema import SdfInformationSchema as SdfInformationSchema
from .resource import SdfCliResource as SdfCliResource
from .version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-sdf", __version__)
