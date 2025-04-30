from collections.abc import Sequence
from pathlib import Path
from typing import Any, NamedTuple, Optional

import click
from dagster_shared.serdes.objects import PluginObjectKey
from dagster_shared.yaml_utils import parse_yaml_with_source_position
from dagster_shared.yaml_utils.source_position import (
    LineCol,
    SourcePosition,
    SourcePositionTree,
    ValueAndSourcePositionTree,
)
from jsonschema import Draft202012Validator, ValidationError
from yaml.scanner import ScannerError

from dagster_dg.cli.check_utils import error_dict_to_formatted_error
from dagster_dg.component import RemotePluginRegistry, get_specified_env_var_deps, get_used_env_vars
from dagster_dg.context import DgContext

COMPONENT_FILE_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "attributes": {"type": "object"},
        "requirements": {
            "type": "object",
            "properties": {"env": {"type": "array", "items": {"type": "string"}}},
            "additionalProperties": False,
        },
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
    object_key: Optional[PluginObjectKey]
    error: ValidationError
    source_position_tree: ValueAndSourcePositionTree


def check_yaml(
    dg_context: DgContext,
    resolved_paths: Sequence[Path],
    validate_requirements: bool,
) -> bool:
    top_level_component_validator = Draft202012Validator(schema=COMPONENT_FILE_SCHEMA)

    validation_errors: list[ErrorInput] = []
    all_specified_env_var_deps = set()

    component_contents_by_key: dict[PluginObjectKey, Any] = {}
    modules_to_fetch = set()
    for component_dir in dg_context.defs_path.rglob("*"):
        if resolved_paths and not any(
            path == component_dir or path in component_dir.parents for path in resolved_paths
        ):
            continue

        component_path = component_dir / "component.yaml"

        if component_path.exists():
            text = component_path.read_text()
            try:
                component_doc_tree = parse_yaml_with_source_position(
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

            if validate_requirements:
                specified_env_var_deps = get_specified_env_var_deps(component_doc_tree.value)
                used_env_vars = get_used_env_vars(component_doc_tree.value)
                all_specified_env_var_deps.update(specified_env_var_deps)

                if used_env_vars - specified_env_var_deps:
                    msg = (
                        "Component uses environment variables that are not specified in the component file: "
                        + ", ".join(used_env_vars - specified_env_var_deps)
                    )

                    validation_errors.append(
                        ErrorInput(
                            None,
                            ValidationError(
                                msg,
                                path=["requirements", "env"],
                            ),
                            component_doc_tree,
                        )
                    )

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
            key = PluginObjectKey.from_typename(qualified_key)
            component_contents_by_key[key] = component_doc_tree

            # We need to fetch components from any modules local to the project because these are
            # not cached with the components from the general environment.
            if key.namespace.startswith(dg_context.defs_module_name):
                modules_to_fetch.add(key.namespace)

    # Fetch the local component types, if we need any local components
    component_registry = RemotePluginRegistry.from_dg_context(
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
        return False
    else:
        click.echo("All components validated successfully.")

        return True
