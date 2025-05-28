from dagster_shared.libraries import DagsterLibraryRegistry

from create_dagster.version import __version__ as __version__

DagsterLibraryRegistry.register("create-dagster", __version__)
