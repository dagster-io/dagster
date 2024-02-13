from dagster._core.libraries import DagsterLibraryRegistry

from .loggers import papertrail_logger
from .version import __version__

DagsterLibraryRegistry.register("dagster-papertrail", __version__)

__all__ = ["papertrail_logger"]
