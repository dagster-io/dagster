from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_soda.component import SodaScanComponent
from dagster_soda.version import __version__

__all__ = [
    "SodaScanComponent",
]

DagsterLibraryRegistry.register("dagster-soda", __version__)
