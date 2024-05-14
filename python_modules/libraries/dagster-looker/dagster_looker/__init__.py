from dagster._core.libraries import DagsterLibraryRegistry

from .asset_decorator import looker_assets as looker_assets
from .version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-looker", __version__)
