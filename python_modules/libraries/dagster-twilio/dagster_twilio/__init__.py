from dagster._core.utils import check_dagster_package_version

from .resources import twilio_resource
from .version import __version__

check_dagster_package_version("dagster-twilio", __version__)

__all__ = ["twilio_resource"]
