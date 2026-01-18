import textwrap
from collections.abc import Sequence
from typing import Literal, Optional, TypeAlias

import click

from dagster_dg_core.utils import format_multiline_str

DgWarningIdentifier: TypeAlias = Literal[
    "cli_config_in_workspace_project",
    "deprecated_user_config_location",
    "deprecated_python_environment",
    "deprecated_dagster_dg_library_entry_point",
    "missing_dg_plugin_module_in_manifest",
    "project_and_activated_venv_mismatch",
    # create-dagster
    "create_dagster_outdated",
]


def emit_warning(
    warning_id: DgWarningIdentifier,
    msg: str,
    suppress_warnings: Optional[Sequence[DgWarningIdentifier]],
    include_suppression_instruction: bool = True,
) -> None:
    if warning_id not in (suppress_warnings or []):
        formatted_main_msg = textwrap.dedent(msg).strip()
        suppression_instruction = format_multiline_str(f"""
            To suppress this warning, add "{warning_id}" to the `cli.suppress_warnings` list in
            your configuration.
        """)
        full_msg = (
            f"{formatted_main_msg}\n\n{suppression_instruction}\n"
            if include_suppression_instruction
            else formatted_main_msg
        )
        click.secho(
            full_msg,
            fg="yellow",
            err=True,
        )
