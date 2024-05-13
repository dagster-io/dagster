from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-looker", __version__)
