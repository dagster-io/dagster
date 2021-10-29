from dagster.core.utils import check_dagster_package_version

from .resources import fivetran_resource
from .ops import fivetran_sync_op
from .version import __version__

check_dagster_package_version("dagster-fivetran", __version__)

__all__ = ["fivetran_connector_resource"]
