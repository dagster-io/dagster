from pathlib import Path
from typing import Any, Dict, NamedTuple, Optional, Sequence, Type, Union, cast

from dagster import _check as check
from dagster._config.pythonic_config.type_check_utils import safe_is_subclass
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.metadata.source_code import (
    CodeReferencesMetadataSet,
    CodeReferencesMetadataValue,
    LocalFileCodeReference,
)
from dagster._model.pydantic_compat_layer import json_schema_from_type
from dagster._record import copy
from dagster._utils.pydantic_yaml import (
    parse_yaml_file_to_pydantic,
    parse_yaml_file_to_pydantic_sequence,
)
from typing_extensions import get_args, get_origin

from .blueprint import Blueprint


def _attach_code_references_to_definitions(blueprint: Blueprint, defs: Definitions) -> Definitions:
    """Attaches code reference metadata pointing to the specified file path to all assets in the
    output blueprint definitions.
    """
    assets_defs = defs.assets or []
    new_assets_defs = []

    source_position_and_key_path = blueprint.source_position
    line_number = source_position_and_key_path.start.line if source_position_and_key_path else None
    file_path = source_position_and_key_path.filename if source_position_and_key_path else None

    if not file_path:
        return defs

    reference = LocalFileCodeReference(
        file_path=file_path,
        line_number=line_number,
    )

    for assets_def in assets_defs:
        if not isinstance(assets_def, AssetsDefinition):
            new_assets_defs.append(assets_def)
            continue

        new_metadata_by_key = {}
        for key in assets_def.metadata_by_key.keys():
            existing_references_meta = CodeReferencesMetadataSet.extract(
                assets_def.metadata_by_key[key]
            )
            existing_references = (
                existing_references_meta.code_references.code_references
                if existing_references_meta.code_references
                else []
            )

            new_metadata_by_key[key] = {
                **assets_def.metadata_by_key[key],
                **CodeReferencesMetadataSet(
                    code_references=CodeReferencesMetadataValue(
                        code_references=[*existing_references, reference],
                    )
                ),
            }

        new_assets_defs.append(
            assets_def.map_asset_specs(
                lambda spec: spec._replace(metadata=new_metadata_by_key[spec.key])
            )
        )
    return copy(defs, assets=new_assets_defs)


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
        per_file_blueprint_type (Union[Type[Blueprint], Type[Sequence[Blueprint]]]): The type
            of blueprint that each of the YAML files are expected to conform to. If a sequence
            type is provided, the function will expect each YAML file to contain a list of
            blueprints.
        resources (Dict[str, Any], optional): A dictionary of resources to be bound to the
            definitions. Defaults to None.

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

    def_sets_with_code_references = [
        _attach_code_references_to_definitions(
            blueprint, blueprint.build_defs_add_context_to_errors()
        )
        for blueprint in blueprints
    ]

    return Definitions.merge(*def_sets_with_code_references, Definitions(resources=resources or {}))


class YamlBlueprintsLoader(NamedTuple):
    """A loader is responsible for loading a set of Dagster definitions from one or more YAML
    files based on a set of supplied blueprints.

    Attributes:
        path (Path | str): The path to the YAML file or directory of YAML files containing the
            blueprints for Dagster definitions.
        per_file_blueprint_type (Union[Type[Blueprint], Sequence[Type[Blueprint]]]): The type
            of blueprint that each of the YAML files are expected to conform to. If a sequence
            type is provided, the function will expect each YAML file to contain a list of
            blueprints.
    """

    path: Path
    per_file_blueprint_type: Union[Type[Blueprint], Type[Sequence[Blueprint]]]

    def load_defs(self, resources: Optional[Dict[str, Any]] = None) -> Definitions:
        """Load Dagster definitions from a YAML file of blueprints.

        Args:
            resources (Dict[str, Any], optional): A dictionary of resources to be bound to the
                definitions. Defaults to None.
        """
        return load_defs_from_yaml(
            path=self.path,
            per_file_blueprint_type=self.per_file_blueprint_type,
            resources=resources,
        )

    def model_json_schema(self) -> Dict[str, Any]:
        """Returns a JSON schema for the model or models that the loader is responsible for loading."""
        return json_schema_from_type(self.per_file_blueprint_type)
