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
    compute_kind: str = Field("compute", description="The kind of the compute function")

    def build_defs(self) -> BlueprintDefinitions:
        @asset(key=self.key, compute_kind=self.compute_kind)
        def blueprint_asset(): ...

        return BlueprintDefinitions(assets=[blueprint_asset])


loader = YamlBlueprintsLoader(
    name="loader",
    path=Path(__file__).parent / "blueprints",
    per_file_blueprint_type=SimpleAssetBlueprint,
)
other_loader = YamlBlueprintsLoader(
    name="other_loader",
    path=Path(__file__).parent / "other_blueprints",
    per_file_blueprint_type=Union[SimpleAssetBlueprint, OtherAssetBlueprint],
)

from dagster import job, op


@op
def my_op(): ...


@job
def my_job():
    my_op()


defs = Definitions.merge(
    loader.get_defs(),
    other_loader.get_defs(),
    Definitions(
        blueprint_managers=[loader, other_loader],
        jobs=[my_job],
    ),
)
