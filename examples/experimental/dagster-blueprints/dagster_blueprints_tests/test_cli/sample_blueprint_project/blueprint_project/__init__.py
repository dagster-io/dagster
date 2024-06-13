from pathlib import Path
from typing import Union

from dagster import Definitions, asset
from dagster_blueprints.blueprint import Blueprint, BlueprintDefinitions
from dagster_blueprints.load_from_yaml import YamlBlueprintsLoader
from pydantic import Field


class OtherAssetBlueprint(Blueprint):
    """Baz."""

    key: str = Field(..., description="The key of the asset blueprint 2.")

    def build_defs(self) -> BlueprintDefinitions:
        @asset(key=self.key)
        def blueprint_asset(): ...

        return BlueprintDefinitions(assets=[blueprint_asset])


class SimpleAssetBlueprint(Blueprint):
    """Defines a simple asset blueprint."""

    key: str = Field(..., description="The key of the asset blueprint.")
    description: str = Field("Test", description="The description of the asset blueprint")

    def build_defs(self) -> BlueprintDefinitions:
        @asset(key=self.key)
        def blueprint_asset(): ...

        return BlueprintDefinitions(assets=[blueprint_asset])


loader = YamlBlueprintsLoader(
    path=Path(__file__).parent / "blueprints", per_file_blueprint_type=SimpleAssetBlueprint
)
other_loader = YamlBlueprintsLoader(
    path=Path(__file__).parent / "other_blueprints",
    per_file_blueprint_type=Union[SimpleAssetBlueprint, OtherAssetBlueprint],
)

defs = Definitions.merge(
    loader.get_defs(),
    other_loader.get_defs(),
    Definitions(
        blueprint_managers=[loader, other_loader],
    ),
)
