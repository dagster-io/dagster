from dagster._core.utils import check_dagster_package_version

from .solids import create_shell_command_op, create_shell_script_op, shell_op
from .utils import execute as execute_shell_command
from .utils import execute_script_file as execute_shell_script
from .version import __version__

check_dagster_package_version("dagster-shell", __version__)

__all__ = [
    "create_shell_command_op",
    "create_shell_script_op",
    "shell_op",
    "execute_shell_command",
    "execute_shell_script",
]
