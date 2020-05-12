from dagster.core.utils import check_dagster_package_version

from .solids import bash_command_solid, bash_script_solid
from .version import __version__

check_dagster_package_version('dagster-bash', __version__)

__all__ = ['bash_command_solid', 'bash_script_solid']
