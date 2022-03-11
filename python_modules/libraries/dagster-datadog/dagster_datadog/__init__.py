from dagster._core.utils import check_dagster_package_version

from .resources import datadog_resource
from .version import __version__

check_dagster_package_version("dagster-datadog", __version__)

__all__ = ["datadog_resource"]
