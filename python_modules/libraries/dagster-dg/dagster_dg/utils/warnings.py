import textwrap
from collections.abc import Sequence
from typing import Literal

import click
from typing_extensions import TypeAlias

from dagster_dg.utils import format_multiline_str

DgWarningIdentifier: TypeAlias = Literal[
    "cli_config_in_workspace_project",
    "deprecated_python_environment",
    "project_and_activated_venv_mismatch",
]


def emit_warning(
    warning_id: DgWarningIdentifier, msg: str, suppress_warnings: Sequence[DgWarningIdentifier]
) -> None:
    if warning_id not in suppress_warnings:
        suppression_instruction = format_multiline_str(f"""
            To suppress this warning, add "{warning_id}" to the `cli.suppress_warnings` list in
            your configuration.
        """)
        full_msg = f"{textwrap.dedent(msg).strip()}\n\n{suppression_instruction}\n"
        click.secho(
            full_msg,
            fg="yellow",
            err=True,
        )
