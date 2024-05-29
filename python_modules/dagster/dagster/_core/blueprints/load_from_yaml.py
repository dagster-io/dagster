import os
from pathlib import Path
from typing import Any, Optional, Type, Union

import jinja2

from dagster import (
    Definitions,
    _check as check,
)
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.metadata.source_code import (
    CodeReferencesMetadataSet,
    CodeReferencesMetadataValue,
    LocalFileCodeReference,
)
from dagster._utils.pydantic_yaml import parse_yaml_file_to_pydantic

from .blueprint import Blueprint, BlueprintDefinitions, DagsterBuildDefinitionsFromConfigError


def _attach_code_references_to_definitions(
    blueprint: Blueprint, defs: BlueprintDefinitions
) -> BlueprintDefinitions:
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
            AssetsDefinition.dagster_internal_init(
                **{
                    **assets_def.get_attributes_dict(),
                    **{
                        "specs": [
                            spec._replace(metadata=new_metadata_by_key[spec.key])
                            for spec in assets_def.specs
                        ]
                    },
                }
            )
        )
    return defs._replace(assets=new_assets_defs)


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

    def resolve_env_var(file_path: Path, key: str, default: Optional[str] = None) -> str:
        out = os.environ.get(key, default)
        if out is None:
            raise DagsterBuildDefinitionsFromConfigError(
                f"Environment variable {key} not set when processing blueprint file {file_path}"
            )
        return out

    def process_jinja_string(file_path: Path, value: Any) -> Any:
        if isinstance(value, str):
            return jinja2.Template(value).render(
                env_var=lambda *args: resolve_env_var(file_path, *args)
            )
        else:
            return value

    blueprints = [
        parse_yaml_file_to_pydantic(
            per_file_blueprint_type,
            file_path.read_text(),
            str(file_path),
            leaf_resolver=lambda value: process_jinja_string(file_path, value),
        )
        for file_path in file_paths
    ]

    def_sets_with_code_references = [
        _attach_code_references_to_definitions(
            blueprint, blueprint.build_defs_add_context_to_errors()
        )
        for blueprint in blueprints
    ]

    return BlueprintDefinitions.merge(*def_sets_with_code_references).to_definitions()
