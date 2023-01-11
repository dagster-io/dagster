from dagster._core.utils import check_dagster_package_version

from .hooks import pagerduty_on_failure as pagerduty_on_failure
from .resources import pagerduty_resource as pagerduty_resource
from .version import __version__ as __version__

check_dagster_package_version("dagster-pagerduty", __version__)
