from create_dagster.version import __version__ as __version__
from dagster_shared.libraries import DagsterLibraryRegistry

DagsterLibraryRegistry.register("create-dagster", __version__)
