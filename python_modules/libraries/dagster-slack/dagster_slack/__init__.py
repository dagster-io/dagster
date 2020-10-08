from dagster.core.utils import check_dagster_package_version

from .resources import slack_resource
from .version import __version__

check_dagster_package_version("dagster-slack", __version__)

__all__ = ["slack_resource"]
