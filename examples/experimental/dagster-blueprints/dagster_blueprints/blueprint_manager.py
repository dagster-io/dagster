from abc import ABC, abstractmethod
from typing import Sequence

from dagster import Definitions
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.metadata.source_code import (
    CodeReferencesMetadataSet,
    CodeReferencesMetadataValue,
    LocalFileCodeReference,
)
from dagster._core.remote_representation.external_data import BlueprintKey

from .blueprint import Blueprint, BlueprintDefinitions


def attach_blueprint_key_to_definitions(
    blueprint_key: BlueprintKey, defs: BlueprintDefinitions
) -> BlueprintDefinitions:
    """Attaches the key of the blueprint to all assets in the output blueprint definitions."""
    assets_defs = defs.assets or []
    new_assets_defs = []

    for assets_def in assets_defs:
        if not isinstance(assets_def, AssetsDefinition):
            new_assets_defs.append(assets_def)
            continue

        new_tags_by_key = {}
        for key in assets_def.tags_by_key.keys():
            new_tags_by_key[key] = {
                **assets_def.tags_by_key[key],
                **{"dagster/blueprint_key": blueprint_key.to_string()},
            }

        new_assets_defs.append(
            AssetsDefinition.dagster_internal_init(
                **{
                    **assets_def.get_attributes_dict(),
                    **{
                        "specs": [
                            spec._replace(tags=new_tags_by_key[spec.key])
                            for spec in assets_def.specs
                        ]
                    },
                }
            )
        )
    return defs._replace(assets=new_assets_defs)


def attach_code_references_to_definitions(
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


class BlueprintManager(ABC):
    """A container for a set of blueprints that can be loaded. Knows how to add,
    update, and delete blueprints within it.

    Users cannot define their own subclasses, because they need to be loadable
    from host processes.
    """

    @abstractmethod
    def get_name(self) -> str: ...

    @abstractmethod
    def add_blueprint(self, identifier: object, blob: str) -> str: ...

    @abstractmethod
    def update_blueprint(self, identifier: object, blob: str) -> str: ...

    # @abstractmethod
    # def delete_blueprint(self, identifier: object, blob: Blob) -> None: ...

    @abstractmethod
    def load_blueprints(self) -> Sequence[Blueprint]: ...

    def get_defs(self) -> Definitions:
        return load_defs_from_blueprint_manager(self)


def load_defs_from_blueprint_manager(manager: BlueprintManager) -> Definitions:
    """Load Dagster definitions from a BlueprintManager object.

    Args:
        manager (BlueprintManager): The BlueprintManager object which is used to
            load the blueprints.

    Returns:
        Definitions: The loaded Dagster Definitions object.
    """
    blueprints = manager.load_blueprints()

    def_sets_with_code_references = [
        attach_blueprint_key_to_definitions(
            BlueprintKey(manager.get_name(), blueprint.get_identifier()),
            attach_code_references_to_definitions(
                blueprint, blueprint.build_defs_add_context_to_errors()
            ),
        )
        for blueprint in blueprints
    ]

    return BlueprintDefinitions.merge(*def_sets_with_code_references).to_definitions()
