from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__

DagsterLibraryRegistry.register("dagit", __version__)
