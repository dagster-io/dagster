from dagster.core.utils import check_dagster_package_version

from .solids import (
    create_shell_command_op,
    create_shell_command_solid,
    create_shell_script_op,
    create_shell_script_solid,
    shell_op,
    shell_solid,
)
from .version import __version__

check_dagster_package_version("dagster-shell", __version__)

__all__ = [
    "create_shell_command_solid",
    "create_shell_script_solid",
    "shell_solid",
    "create_shell_command_op",
    "create_shell_script_op",
    "shell_op",
]
