from dagster.core.utils import check_dagster_package_version

from .loggers import papertrail_logger
from .version import __version__

check_dagster_package_version("dagster-papertrail", __version__)

__all__ = ["papertrail_logger"]
