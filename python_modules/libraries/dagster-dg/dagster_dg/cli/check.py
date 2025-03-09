import contextlib
import subprocess
import sys
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any, NamedTuple, Optional

import click
from jsonschema import Draft202012Validator, ValidationError
from yaml.scanner import ScannerError

from dagster_dg.cli.check_utils import error_dict_to_formatted_error
from dagster_dg.cli.dev import create_temp_workspace_file, format_forwarded_option
from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.component import RemoteComponentRegistry
from dagster_dg.component_key import ComponentKey
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.utils import DgClickCommand, DgClickGroup, exit_with_error, pushd
from dagster_dg.yaml_utils import parse_yaml_with_source_positions
from dagster_dg.yaml_utils.source_position import (
    LineCol,
    SourcePosition,
    SourcePositionTree,
    ValueAndSourcePositionTree,
)


@click.group(name="check", cls=DgClickGroup)
def check_group():
    """Commands for checking the integrity of your Dagster code."""


# ########################
# ##### COMPONENT
# ########################

COMPONENT_FILE_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "attributes": {"type": "object"},
    },
    "additionalProperties": False,
}


def _scaffold_value_and_source_position_tree(
    filename: str, row: int, col: int
) -> ValueAndSourcePositionTree:
    return ValueAndSourcePositionTree(
        value=None,
        source_position_tree=SourcePositionTree(
            position=SourcePosition(
                filename=filename, start=LineCol(row, col), end=LineCol(row, col)
            ),
            children={},
        ),
    )


class ErrorInput(NamedTuple):
    component_name: Optional[ComponentKey]
    error: ValidationError
    source_position_tree: ValueAndSourcePositionTree


@check_group.command(name="yaml", cls=DgClickCommand)
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@dg_global_options
def check_yaml_command(
    paths: Sequence[str],
    **global_options: object,
) -> None:
    """Check component.yaml files against their schemas, showing validation errors."""
    resolved_paths = [Path(path).absolute() for path in paths]
    top_level_component_validator = Draft202012Validator(schema=COMPONENT_FILE_SCHEMA)

    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    validation_errors: list[ErrorInput] = []

    component_contents_by_key: dict[ComponentKey, Any] = {}
    modules_to_fetch = set()
    for component_dir in dg_context.defs_path.iterdir():
        if resolved_paths and not any(
            path == component_dir or path in component_dir.parents for path in resolved_paths
        ):
            continue

        component_path = component_dir / "component.yaml"

        if component_path.exists():
            text = component_path.read_text()
            try:
                component_doc_tree = parse_yaml_with_source_positions(
                    text, filename=str(component_path)
                )
            except ScannerError as se:
                validation_errors.append(
                    ErrorInput(
                        None,
                        ValidationError(f"Unable to parse YAML: {se.context}, {se.problem}"),
                        _scaffold_value_and_source_position_tree(
                            filename=str(component_path),
                            row=se.problem_mark.line + 1 if se.problem_mark else 1,
                            col=se.problem_mark.column + 1 if se.problem_mark else 1,
                        ),
                    )
                )
                continue

            # First, validate the top-level structure of the component file
            # (type and params keys) before we try to validate the params themselves.
            top_level_errs = list(
                top_level_component_validator.iter_errors(component_doc_tree.value)
            )
            for err in top_level_errs:
                validation_errors.append(ErrorInput(None, err, component_doc_tree))
            if top_level_errs:
                continue

            raw_key = component_doc_tree.value.get("type")
            component_instance_module = dg_context.get_component_instance_module_name(
                component_dir.name
            )
            qualified_key = (
                f"{component_instance_module}{raw_key}" if raw_key.startswith(".") else raw_key
            )
            key = ComponentKey.from_typename(qualified_key)
            component_contents_by_key[key] = component_doc_tree

            # We need to fetch components from any modules local to the project because these are
            # not cached with the components from the general environment.
            if key.namespace.startswith(dg_context.defs_module_name):
                modules_to_fetch.add(key.namespace)

    # Fetch the local component types, if we need any local components
    component_registry = RemoteComponentRegistry.from_dg_context(
        dg_context, extra_modules=list(modules_to_fetch)
    )
    for key, component_doc_tree in component_contents_by_key.items():
        try:
            json_schema = component_registry.get(key).component_schema or {}

            v = Draft202012Validator(json_schema)
            for err in v.iter_errors(component_doc_tree.value["attributes"]):
                validation_errors.append(ErrorInput(key, err, component_doc_tree))
        except KeyError:
            # No matching component type found
            validation_errors.append(
                ErrorInput(
                    None,
                    ValidationError(f"Component type '{key.to_typename()}' not found."),
                    component_doc_tree,
                )
            )
    if validation_errors:
        for key, error, component_doc_tree in validation_errors:
            click.echo(
                error_dict_to_formatted_error(
                    key,
                    error,
                    source_position_tree=component_doc_tree.source_position_tree,
                    prefix=["attributes"] if key else [],
                )
            )
        click.get_current_context().exit(1)
    else:
        click.echo("All components validated successfully.")


@check_group.command(name="defs", cls=DgClickCommand)
@click.option(
    "--log-level",
    help="Set the log level for dagster services.",
    show_default=True,
    default="warning",
    type=click.Choice(["critical", "error", "warning", "info", "debug"], case_sensitive=False),
)
@click.option(
    "--log-format",
    type=click.Choice(["colored", "json", "rich"], case_sensitive=False),
    show_default=True,
    required=False,
    default="colored",
    help="Format of the logs for dagster services",
)
@click.option(
    "--verbose",
    "-v",
    flag_value=True,
    default=False,
    help="Show verbose error messages, including system frames in stack traces.",
)
@dg_global_options
@click.pass_context
def check_definitions_command(
    context: click.Context,
    log_level: str,
    log_format: str,
    verbose: bool,
    **global_options: Mapping[str, object],
) -> None:
    """Loads and validates your Dagster definitions using a Dagster instance.

    If run inside a deployment directory, this command will launch all code locations in the
    deployment. If launched inside a code location directory, it will launch only that code
    location.

    When running, this command sets the environment variable `DAGSTER_IS_DEFS_VALIDATION_CLI=1`.
    This environment variable can be used to control the behavior of your code in validation mode.

    This command returns an exit code 1 when errors are found, otherwise an exit code 0.

    """
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.for_workspace_or_project_environment(Path.cwd(), cli_config)

    forward_options = [
        *format_forwarded_option("--log-level", log_level),
        *format_forwarded_option("--log-format", log_format),
        *(["--verbose"] if verbose else []),
    ]

    with (
        pushd(dg_context.root_path),
        create_validate_cmd(dg_context, forward_options) as (cmd_location, cmd, workspace_file),
    ):
        print(f"Using {cmd_location}")  # noqa: T201
        if workspace_file:  # only non-None deployment context
            cmd.extend(["--workspace", workspace_file])

        print(" ".join(cmd))  # noqa: T201

        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            sys.exit(result.returncode)

    click.echo("All definitions loaded successfully.")


class CommandArgs(NamedTuple):
    cmd_location: str
    cmd: list[str]
    workspace_file: Optional[str]


@contextlib.contextmanager
def create_validate_cmd(dg_context: DgContext, forward_options: list[str]) -> Iterator[CommandArgs]:
    val_args = ["definitions", "validate", *forward_options]
    if dg_context.is_project:
        # In a code location context, we can just run `dagster definitions validate` directly, using `dagster` from the
        # code location's environment.
        cmd = ["uv", "run", "dagster", *val_args]
        cmd_location = dg_context.get_executable("dagster")
        with create_temp_workspace_file(dg_context) as temp_workspace_file:
            yield CommandArgs(
                cmd_location=str(cmd_location), cmd=cmd, workspace_file=temp_workspace_file
            )
        # Still need to get test_validate_command_project_context_success to work
        # yield CommandArgs(cmd_location=str(cmd_location), cmd=cmd, workspace_file=None)
    elif dg_context.is_workspace:
        # In a workspace context, dg validate will construct a temporary
        # workspace file that points at all defined code locations and invoke:
        #
        #     uv tool run --with dagster-webserver dagster definitions validate
        with create_temp_workspace_file(dg_context) as temp_workspace_file:
            yield CommandArgs(
                cmd=["uv", "tool", "run", "dagster", *val_args],
                cmd_location="ephemeral dagster definitions validate",
                workspace_file=temp_workspace_file,
            )
    else:
        exit_with_error("This command must be run inside a code location or deployment directory.")
