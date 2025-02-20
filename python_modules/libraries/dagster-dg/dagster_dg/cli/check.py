from collections.abc import Sequence
from pathlib import Path
from typing import Any, NamedTuple, Optional

import click
from jsonschema import Draft202012Validator, ValidationError
from yaml.scanner import ScannerError

from dagster_dg.cli.check_utils import error_dict_to_formatted_error
from dagster_dg.cli.global_options import dg_global_options
from dagster_dg.component import RemoteComponentRegistry
from dagster_dg.component_key import ComponentKey, LocalComponentKey
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.utils import DgClickCommand, DgClickGroup
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
@click.pass_context
def check_yaml_command(
    context: click.Context,
    paths: Sequence[str],
    **global_options: object,
) -> None:
    """Check component.yaml files against their schemas, showing validation errors."""
    resolved_paths = [Path(path).absolute() for path in paths]
    top_level_component_validator = Draft202012Validator(schema=COMPONENT_FILE_SCHEMA)

    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    validation_errors: list[ErrorInput] = []

    component_contents_by_key: dict[ComponentKey, Any] = {}
    local_component_dirs = set()
    for component_dir in dg_context.components_path.iterdir():
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

            component_key = ComponentKey.from_typename(
                component_doc_tree.value.get("type"), dirpath=component_path.parent
            )
            component_contents_by_key[component_key] = component_doc_tree
            if isinstance(component_key, LocalComponentKey):
                local_component_dirs.add(component_dir)

    # Fetch the local component types, if we need any local components
    component_registry = RemoteComponentRegistry.from_dg_context(
        dg_context, local_component_type_dirs=list(local_component_dirs)
    )
    for component_key, component_doc_tree in component_contents_by_key.items():
        try:
            json_schema = component_registry.get(component_key).component_schema or {}

            v = Draft202012Validator(json_schema)
            for err in v.iter_errors(component_doc_tree.value["attributes"]):
                validation_errors.append(ErrorInput(component_key, err, component_doc_tree))
        except KeyError:
            # No matching component type found
            validation_errors.append(
                ErrorInput(
                    None,
                    ValidationError(
                        f"Component type '{component_key.to_typename()}' not found in {component_key.python_file}."
                        if isinstance(component_key, LocalComponentKey)
                        else f"Component type '{component_key.to_typename()}' not found."
                    ),
                    component_doc_tree,
                )
            )
    if validation_errors:
        for component_key, error, component_doc_tree in validation_errors:
            click.echo(
                error_dict_to_formatted_error(
                    component_key,
                    error,
                    source_position_tree=component_doc_tree.source_position_tree,
                    prefix=["attributes"] if component_key else [],
                )
            )
        context.exit(1)
    else:
        click.echo("All components validated successfully.")
