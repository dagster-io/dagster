from dagster._core.libraries import DagsterLibraryRegistry

from dagster_obstore.version import __version__

DagsterLibraryRegistry.register("dagster-obstore", __version__)
