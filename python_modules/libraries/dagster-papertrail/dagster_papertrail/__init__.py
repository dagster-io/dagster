from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_papertrail.loggers import papertrail_logger
from dagster_papertrail.version import __version__

DagsterLibraryRegistry.register("dagster-papertrail", __version__)

__all__ = ["papertrail_logger"]
