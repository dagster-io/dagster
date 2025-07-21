import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper


def _context_prompt(dg_context: DgContext):
    return f"""
This session was started via the Dagster CLI `dg`. The following context will help you work with the user to accomplish their goals using the Dagster library and `dg` CLI.

# Dagster

Dagster is a data orchestration platform for building, testing, and monitoring data pipelines.

# Definitions

The Dagster library operates over definitions created by the user. The core definition types are:

* Assets
* Asset Checks
* Jobs
* Schedules
* Sensors
* Resources

# Assets

The primary Dagster definition type, representing a data object (table, file, model) that's produced by computation.
Assets have the following identifying properties:
* `key` - The unique identifier for the asset.
* `group` - The group the asset belongs to.
* `kind` - What type of asset it is (can be multiple kinds).
* `tags` - User defined key value pairs.

## Asset Selection Syntax

Assets can be selected using the following syntax:
- key:"value" - exact key match
- key:"prefix_*" - wildcard key matching
- tag:"name" - exact tag match
- tag:"name"="value" - tag with specific value
- owner:"name" - filter by owner
- group:"name" - filter by group
- kind:"type" - filter by asset kind


# Components
An abstraction for creating Dagster Definitions.
Component instances are most commonly defined in defs.yaml files. These files abide by the following required schema:

```yaml
type: module.ComponentType # The Component type to instantiate
attributes: ... # The attributes to pass to the Component. The Component type defines the schema of these attributes.
```
Multiple component instances can be defined in a yaml file, separated by `---`.

Component instances can also be defined in python files using the `@component_instance` decorator.

# Project Layout

The project root is `{dg_context.root_path}`.
The defs path is `{dg_context.defs_path}`. Dagster definitions are defined via yaml and py files in this directory.

# `dg` Dagster CLI
The `dg` CLI is a tool for managing Dagster projects and workspaces.

## Essential Commands

```bash
# Validation
dg check yaml # Validate yaml files according to their schema (fast)
dg check defs # Validate definitions by loading them fully (slower)

# Scaffolding
dg scaffold defs <component type> # Create an instance of a Component type. Available types found via `dg list components`.
dg scaffold defs dagster.<asset|job|schedule|sensor> # Create a new definition of a given type.
dg scaffold component <name> # Create a new custom Component type

# Searching
dg list defs # Show project definitions
dg list defs --assets <asset selection> # Show selected asset definitions
dg list component-tree # Show the component tree
dg list components # Show available component types
dg docs component <component type> # Show documentation for a component type
```
* The `dg` CLI will be effective in accomplishing tasks. Use --help to better understand how to use commands.
* Prefer `dg list defs` over searching the files system when looking for Dagster definitions.
* Use the --json flag to get structured output.
    """


def _find_claude(dg_context: DgContext) -> Optional[str]:
    try:  # on PATH
        subprocess.run(
            ["claude", "--version"],
            check=False,
        )
        return "claude"
    except FileNotFoundError:
        pass

    try:  # check for alias (auto-updating version recommends registering an alias instead of putting on PATH)
        result = subprocess.run(
            [os.getenv("SHELL", "bash"), "-ic", "type claude"],
            capture_output=True,
            text=True,
            check=False,
        )
        path_match = re.search(r"(/[^\s`\']+)", result.stdout)
        if path_match:
            return path_match.group(1)
    except FileNotFoundError:
        pass

    return None


@click.command(
    name="ai",
    cls=DgClickCommand,
    help="[Experimental] Start a Dagster focused CLI agent session.",
)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def ai_command(
    target_path: Path,
    **other_options: object,
) -> None:
    cli_config = normalize_cli_config(other_options, click.get_current_context())
    dg_context = DgContext.for_workspace_or_project_environment(target_path, cli_config)

    click.echo("WARNING: This feature is under active development.")
    click.echo("Features and behavior may change significantly in future versions.\n")
    click.echo("Checking for supported CLI agent...\n")
    claude_path = _find_claude(dg_context)
    if not claude_path:
        click.echo("No supported CLI agent found.")
        click.echo("Currently supported agents:")
        click.echo("  - Claude Code: https://claude.ai/code")
        sys.exit(1)

    click.echo(f"Found {claude_path}. Starting session with context...\n")
    subprocess.run(
        [claude_path, _context_prompt(dg_context)],
        check=False,
    )
