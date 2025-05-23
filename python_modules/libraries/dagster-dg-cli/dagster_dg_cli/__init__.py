from dagster_shared.libraries import DagsterLibraryRegistry

from .version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-dg-cli", __version__)