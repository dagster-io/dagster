from pathlib import Path

from dagster import Definitions, asset
from dagster_blueprints.blueprint import Blueprint, BlueprintDefinitions
from dagster_blueprints.load_from_yaml import YamlBlueprintsLoader


class SimpleAssetBlueprint(Blueprint):
    key: str

    def build_defs(self) -> BlueprintDefinitions:
        @asset(key=self.key)
        def blueprint_asset(): ...

        return BlueprintDefinitions(assets=[blueprint_asset])


loader = YamlBlueprintsLoader(
    path=Path(__file__).parent / "blueprints", per_file_blueprint_type=SimpleAssetBlueprint
)
other_loader = YamlBlueprintsLoader(
    path=Path(__file__).parent / "other_blueprints", per_file_blueprint_type=SimpleAssetBlueprint
)

defs = Definitions.merge(
    loader.get_defs(),
    other_loader.get_defs(),
    Definitions(
        blueprint_managers=[loader, other_loader],
    ),
)
