from dagster.core.utils import check_dagster_package_version

from .executor import celery_executor
from .version import __version__

check_dagster_package_version("dagster-celery", __version__)

__all__ = ["celery_executor"]
