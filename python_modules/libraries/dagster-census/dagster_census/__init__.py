from dagster._core.libraries import DagsterLibraryRegistry

from .ops import census_trigger_sync_op
from .resources import CensusResource, census_resource
from .types import CensusOutput
from .version import __version__

DagsterLibraryRegistry.register("dagster-census", __version__)

__all__ = [
    "CensusResource",
    "CensusOutput",
    "census_resource",
    "census_trigger_sync_op",
]
