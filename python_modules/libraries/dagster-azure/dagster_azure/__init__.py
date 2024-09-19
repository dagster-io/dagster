from dagster._core.libraries import DagsterLibraryRegistry

from dagster_azure.version import __version__

DagsterLibraryRegistry.register("dagster-azure", __version__)
