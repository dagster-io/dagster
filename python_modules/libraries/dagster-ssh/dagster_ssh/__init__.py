from dagster.core.utils import check_dagster_package_version

from .resources import ssh_resource
from .solids import sftp_solid
from .version import __version__

check_dagster_package_version('dagster-ssh', __version__)

__all__ = ['ssh_resource', 'sftp_solid']
