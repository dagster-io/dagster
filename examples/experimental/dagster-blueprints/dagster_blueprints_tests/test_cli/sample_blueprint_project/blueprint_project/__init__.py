from pathlib import Path

from dagster import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster_blueprints.blueprint import Blueprint
from dagster_blueprints.load_from_yaml import YamlBlueprintsLoader


class SimpleAssetBlueprint(Blueprint):
    key: str

    def build_defs(self) -> Definitions:
        @asset(key=self.key)
        def blueprint_asset(): ...

        return Definitions(assets=[blueprint_asset])


loader = YamlBlueprintsLoader(
    path=Path(__file__).parent / "blueprints", per_file_blueprint_type=SimpleAssetBlueprint
)
other_loader = YamlBlueprintsLoader(
    path=Path(__file__).parent / "other_blueprints", per_file_blueprint_type=SimpleAssetBlueprint
)
