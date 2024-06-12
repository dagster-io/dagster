from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Type, Union, cast

from dagster import (
    Definitions,
    _check as check,
)
from dagster._config.pythonic_config.type_check_utils import safe_is_subclass
from dagster._model.pydantic_compat_layer import json_schema_from_type
from dagster._utils.pydantic_yaml import (
    parse_yaml_file_to_pydantic,
    parse_yaml_file_to_pydantic_sequence,
)
from typing_extensions import get_args, get_origin

from .blueprint import Blueprint, BlueprintDefinitions
from .blueprint_manager import BlueprintManager, attach_code_references_to_definitions


def load_blueprints_from_yaml(
    *,
    path: Union[Path, str],
    per_file_blueprint_type: Union[Type[Blueprint], Type[Sequence[Blueprint]]],
) -> Sequence[Blueprint]:
    """Load blueprints from a YAML file or directory of YAML files.

    Args:
        path (Path | str): The path to the YAML file or directory of YAML files containing the
            blueprints for Dagster definitions.
        per_file_blueprint_type (Union[Type[Blueprint], Sequence[Type[Blueprint]]]): The type
            of blueprint that each of the YAML files are expected to conform to. If a sequence
            type is provided, the function will expect each YAML file to contain a list of
            blueprints.

    Returns:
        Sequence[Blueprint]: The loaded blueprints.
    """
    resolved_path = Path(path)
    check.invariant(resolved_path.exists(), f"No file or directory at path: {resolved_path}")
    file_paths: list[Path]
    if resolved_path.is_file():
        file_paths = [resolved_path]
    else:
        file_paths = list(resolved_path.rglob("*.yaml")) + list(resolved_path.rglob("*.yml"))

    origin = get_origin(per_file_blueprint_type)
    if safe_is_subclass(origin, Sequence):
        args = get_args(per_file_blueprint_type)
        check.invariant(
            args and len(args) == 1,
            "Sequence type annotation must have a single Blueprint type argument",
        )

        # flatten the list of blueprints from all files
        blueprints = [
            blueprint
            for file_path in file_paths
            for blueprint in parse_yaml_file_to_pydantic_sequence(
                args[0], file_path.read_text(), str(file_path)
            )
        ]

    else:
        blueprints = [
            parse_yaml_file_to_pydantic(
                cast(Type[Blueprint], per_file_blueprint_type),
                file_path.read_text(),
                str(file_path),
            )
            for file_path in file_paths
        ]

    return blueprints


def load_defs_from_yaml(
    *,
    path: Union[Path, str],
    per_file_blueprint_type: Union[Type[Blueprint], Type[Sequence[Blueprint]]],
    resources: Optional[Dict[str, Any]] = None,
) -> Definitions:
    """Load Dagster definitions from a YAML file of blueprints.

    Args:
        path (Path | str): The path to the YAML file or directory of YAML files containing the
            blueprints for Dagster definitions.
        per_file_blueprint_type (Union[Type[Blueprint], Sequence[Type[Blueprint]]]): The type
            of blueprint that each of the YAML files are expected to conform to. If a sequence
            type is provided, the function will expect each YAML file to contain a list of
            blueprints.
        resources (Dict[str, Any], optional): A dictionary of resources to be bound to the
            definitions. Defaults to None.

    Returns:
        Definitions: The loaded Dagster Definitions object.
    """
    blueprints = load_blueprints_from_yaml(
        path=path, per_file_blueprint_type=per_file_blueprint_type
    )

    def_sets_with_code_references = [
        attach_code_references_to_definitions(
            blueprint, blueprint.build_defs_add_context_to_errors()
        )
        for blueprint in blueprints
    ]

    return BlueprintDefinitions.merge(
        *def_sets_with_code_references, BlueprintDefinitions(resources=resources or {})
    ).to_definitions()


@dataclass(frozen=True)
class YamlBlueprintsLoader(BlueprintManager):
    """A loader is responsible for loading a set of Dagster definitions from one or more YAML
    files based on a set of supplied blueprints.
    """

    path: Path
    per_file_blueprint_type: Union[Type[Blueprint], Type[Sequence[Blueprint]]]

    def get_name(self) -> str:
        return self.path.name

    def load_blueprints(self) -> Sequence[Blueprint]:
        return load_blueprints_from_yaml(
            path=self.path, per_file_blueprint_type=self.per_file_blueprint_type
        )

    def model_json_schema(self) -> Dict[str, Any]:
        """Returns a JSON schema for the model or models that the loader is responsible for loading."""
        return json_schema_from_type(self.per_file_blueprint_type)
