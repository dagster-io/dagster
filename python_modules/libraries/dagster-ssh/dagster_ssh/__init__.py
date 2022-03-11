from dagster._core.utils import check_dagster_package_version

from .resources import SSHResource, ssh_resource
from .version import __version__

check_dagster_package_version("dagster-ssh", __version__)

__all__ = ["ssh_resource", "SSHResource"]
