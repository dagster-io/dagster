from dagit.version import __version__
from dagster_shared.libraries import DagsterLibraryRegistry

DagsterLibraryRegistry.register("dagit", __version__)
