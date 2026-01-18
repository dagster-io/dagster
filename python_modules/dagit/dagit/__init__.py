from dagster_shared.libraries import DagsterLibraryRegistry

from dagit.version import __version__

DagsterLibraryRegistry.register("dagit", __version__)
