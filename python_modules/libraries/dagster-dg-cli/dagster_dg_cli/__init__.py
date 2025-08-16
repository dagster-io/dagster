from dagster_dg_cli.version import __version__ as __version__
from dagster_shared.libraries import DagsterLibraryRegistry

DagsterLibraryRegistry.register("dagster-dg-cli", __version__)
