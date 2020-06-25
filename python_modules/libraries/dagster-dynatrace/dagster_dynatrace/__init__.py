from dagster.core.utils import check_dagster_package_version

from .client import DTClient
from .resources import dynatrace_resource
from .version import __version__

check_dagster_package_version('dagster-dynatrace', __version__)

__all__ = ['dynatrace_resource']
