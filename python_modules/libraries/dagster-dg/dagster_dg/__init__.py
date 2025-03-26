from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_dg.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-dg", __version__)
