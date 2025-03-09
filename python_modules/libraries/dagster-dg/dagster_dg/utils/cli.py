import subprocess
from collections.abc import Sequence

import click

from dagster_dg.cli.dev import temp_workspace_file
from dagster_dg.context import DgContext
from dagster_dg.utils import exit_with_error, pushd


def run_dagster_command_with_workspace(dg_context: DgContext, args: Sequence[str]):
    temp_workspace_file_cm = temp_workspace_file(dg_context)

    # In a project context, we can just run the command directly, using `dagster` from the
    # project's environment.
    if dg_context.is_project:
        cmd_location = dg_context.get_executable("dagster")
        if dg_context.use_dg_managed_environment:
            cmd = ["uv", "run", "dagster", *args]
        else:
            cmd = [cmd_location, *args]

    # In a workspace context, construct a temporary
    # workspace file that points at all defined projects.
    elif dg_context.is_workspace:
        cmd = [
            "uv",
            "tool",
            "run",
            "dagster",
            *args,
        ]
        cmd_location = "ephemeral dagster"
    else:
        exit_with_error("This command must be run inside a project or workspace directory.")
    with pushd(dg_context.root_path), temp_workspace_file_cm as workspace_file:
        click.echo(f"Using {cmd_location}")
        if workspace_file:  # only non-None deployment context
            cmd.extend(["--workspace", workspace_file])
        subprocess.run(cmd, check=True)
