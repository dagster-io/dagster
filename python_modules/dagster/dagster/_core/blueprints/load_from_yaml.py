from pathlib import Path
from typing import Type, Union

from dagster import (
    Definitions,
    _check as check,
)
from dagster._utils.pydantic_yaml import parse_yaml_file_to_pydantic

from .blueprint import Blueprint, BlueprintDefinitions


def load_defs_from_yaml(
    *, path: Union[Path, str], per_file_blueprint_type: Type[Blueprint]
) -> Definitions:
    """Load Dagster definitions from a YAML file of blueprints.

    Args:
        path (Path | str): The path to the YAML file or directory of YAML files containing the
            blueprints for Dagster definitions.
        per_file_blueprint_type (type[Blueprint]): The type of blueprint that each of the YAML
            files are expected to conform to.

    Returns:
        Definitions: The loaded Dagster Definitions object.
    """
    resolved_path = Path(path)
    check.invariant(resolved_path.exists(), f"No file or directory at path: {resolved_path}")
    file_paths: list[Path]
    if resolved_path.is_file():
        file_paths = [resolved_path]
    else:
        file_paths = list(resolved_path.rglob("*.yaml")) + list(resolved_path.rglob("*.yml"))

    blueprints = [
        parse_yaml_file_to_pydantic(per_file_blueprint_type, file_path.read_text(), str(file_path))
        for file_path in file_paths
    ]

    def_sets = [blueprints.build_defs_add_context_to_errors() for blueprints in blueprints]

    return BlueprintDefinitions.merge(*def_sets).to_definitions()
