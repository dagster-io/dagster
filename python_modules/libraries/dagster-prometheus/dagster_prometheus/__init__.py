from dagster.core.utils import check_dagster_package_version

from .resources import prometheus_resource
from .version import __version__

check_dagster_package_version("dagster-prometheus", __version__)

__all__ = ["prometheus_resource"]
