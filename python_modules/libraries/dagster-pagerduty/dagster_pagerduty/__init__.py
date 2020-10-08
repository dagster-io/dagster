from dagster.core.utils import check_dagster_package_version

from .resources import pagerduty_resource
from .version import __version__

check_dagster_package_version("dagster-pagerduty", __version__)

__all__ = ["pagerduty_resource"]
