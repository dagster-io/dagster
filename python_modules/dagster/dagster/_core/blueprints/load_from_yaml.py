import os
from pathlib import Path
from typing import Type, Union

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

from .blueprint import Blueprint, BlueprintDefinitions


def _attach_code_references_to_definitions(
    file_path: Path, blueprint: BlueprintDefinitions
) -> BlueprintDefinitions:
    """Attaches code reference metadata pointing to the specified file path to all assets in the
    output blueprint definitions.
    """
    assets_defs = blueprint.assets or []
    new_assets_defs = []

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
                        code_references=[
                            *existing_references,
                            LocalFileCodeReference(file_path=os.fspath(file_path)),
                        ],
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
    return blueprint._replace(assets=new_assets_defs)


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

    blueprints = {
        file_path: parse_yaml_file_to_pydantic(
            per_file_blueprint_type, file_path.read_text(), str(file_path)
        )
        for file_path in file_paths
    }

    def_sets = {
        file_path: blueprint.build_defs_add_context_to_errors()
        for file_path, blueprint in blueprints.items()
    }
    def_sets_with_code_references = [
        _attach_code_references_to_definitions(file_path, def_set)
        for file_path, def_set in def_sets.items()
    ]

    return BlueprintDefinitions.merge(*def_sets_with_code_references).to_definitions()
