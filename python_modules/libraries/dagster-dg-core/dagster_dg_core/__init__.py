from dagster_dg_core.version import __version__ as __version__
from dagster_shared.libraries import DagsterLibraryRegistry

DagsterLibraryRegistry.register("dagster-dg-core", __version__)
