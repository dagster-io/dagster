from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dagster import _check as check
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.factory.executable import (
    AssetGraphExecutable,
    AssetGraphExecutionContext,
    AssetGraphExecutionResult,
)
from dagster._nope.project import NopeProject
from pydantic import BaseModel, ValidationError


def load_yaml(path: str) -> dict:
    with open(path, "r") as file:
        return yaml.safe_load(file)


def load_yaml_to_pydantic(yaml_path: str, pydantic_class) -> BaseModel:
    """Reads a YAML file, ensures its schema is compatible with a given Pydantic class,
    and returns an instance of that Pydantic class.

    :param yaml_path: The path to the YAML file to be loaded.
    :param pydantic_class: The Pydantic class to validate against.
    :return: An instance of the Pydantic class with the loaded data.
    :raises ValueError: If the YAML data does not match the schema.
    """
    data = load_yaml(yaml_path)
    try:
        instance = pydantic_class(**data)
        return instance

    except (yaml.YAMLError, ValidationError) as error:
        raise ValueError(f"Failed to parse YAML or validate schema: {error}")


class BespokeELTAssetManifest(BaseModel):
    deps: Optional[List[str]]


class BespokeELTInvocationTargetManifest(BaseModel):
    name: str
    target: str
    source: str
    destination: str
    assets: Dict[str, BespokeELTAssetManifest]


class HighLevelDSLGroupFileManifest(BaseModel):
    invocations: List[BespokeELTInvocationTargetManifest]


class HighLevelDSLManifest(BaseModel):
    group_name: str
    manifest_file: HighLevelDSLGroupFileManifest


def get_single_yaml_file(path: Path) -> Path:
    yaml_files = {}
    for file_path in path.iterdir():
        # python_files = {}
        if file_path.suffix == ".yaml":
            yaml_files[file_path.stem] = file_path

    if len(yaml_files) != 1:
        raise Exception(f"Expected exactly one yaml file in {path}, found {yaml_files}")
    return next(iter(yaml_files.values()))


class HighLevelDSLNopeProject(NopeProject):
    @classmethod
    def make_definitions(cls, defs_path: Path) -> Definitions:
        group_manifest_path = get_single_yaml_file(defs_path)
        group_file_manifest = check.inst(
            load_yaml_to_pydantic(
                str(group_manifest_path.resolve()), HighLevelDSLGroupFileManifest
            ),
            HighLevelDSLGroupFileManifest,
        )
        return DefinitionsBuilder().build(
            HighLevelDSLManifest(
                group_name=group_manifest_path.stem, manifest_file=group_file_manifest
            )
        )


class ManifestSource:
    def get_manifest(self) -> HighLevelDSLManifest:
        raise NotImplementedError("Subclasses must implement this method.")


class InMemoryManifestSource(ManifestSource):
    def __init__(self, manifest: HighLevelDSLManifest):
        self.manifest = manifest

    def get_manifest(self) -> HighLevelDSLManifest:
        return self.manifest


class HighLevelDSLFileSystemManifestSource(ManifestSource):
    def __init__(self, path: Path):
        self.path = path

    def get_manifest(self) -> HighLevelDSLManifest:
        single_group_yaml_file = get_single_yaml_file(self.path)
        group_file_manifest = check.inst(
            load_yaml_to_pydantic(str(single_group_yaml_file), HighLevelDSLGroupFileManifest),
            HighLevelDSLGroupFileManifest,
        )
        return HighLevelDSLManifest(group_name=self.path.stem, manifest_file=group_file_manifest)


class DefinitionsBuilder:
    def build(self, manifest: HighLevelDSLManifest) -> Definitions:
        # return make_definitions_from_manifest(manifest)
        manifest_file = manifest.manifest_file
        assert isinstance(manifest_file, HighLevelDSLGroupFileManifest)
        assets_defs = []
        for invocation in manifest_file.invocations:
            assets_defs.append(
                BespokeELTExecutable(
                    group_name=manifest.group_name, manifest=invocation
                ).to_assets_def()
            )
        return Definitions(assets_defs)


class BespokeELTExecutable(AssetGraphExecutable):
    def __init__(self, group_name: str, manifest: BespokeELTInvocationTargetManifest):
        specs = [
            AssetSpec(key=asset_key, group_name=group_name) for asset_key in manifest.assets.keys()
        ]
        super().__init__(specs=specs)

    def execute(self, context: AssetGraphExecutionContext) -> AssetGraphExecutionResult:
        raise NotImplementedError("Not implemented")


def make_definitions_from_file_system() -> Definitions:
    return DefinitionsBuilder().build(
        HighLevelDSLFileSystemManifestSource(
            path=Path(__file__).resolve().parent / Path("high_level_defs")
        ).get_manifest()
    )


def nope_definitions_pipeline(manifest_source: ManifestSource) -> Definitions:
    return DefinitionsBuilder().build(manifest_source.get_manifest())


def make_definitions_from_python_api() -> Definitions:
    return nope_definitions_pipeline(
        manifest_source=InMemoryManifestSource(
            HighLevelDSLManifest(
                group_name="group_a",
                manifest_file=HighLevelDSLGroupFileManifest(
                    invocations=[
                        BespokeELTInvocationTargetManifest(
                            name="transform_and_load",
                            target="bespoke_elt",
                            source="file://example/file.csv",
                            destination="s3://bucket/file.csv",
                            assets={
                                "root_one": BespokeELTAssetManifest(deps=None),
                                "root_two": BespokeELTAssetManifest(deps=None),
                            },
                        )
                    ]
                ),
            )
        )
    )
    # return DefinitionsBuilder().build(
    #     HighLevelDSLManifest(
    #         manifest_file=HighLevelDSLGroupFileManifest(
    #             invocations=[
    #                 BespokeELTInvocationTargetManifest(
    #                     name="transform_and_load",
    #                     target="bespoke_elt",
    #                     source="file://example/file.csv",
    #                     destination="s3://bucket/file.csv",
    #                     assets={
    #                         "root_one": BespokeELTAssetManifest(deps=None),
    #                         "root_two": BespokeELTAssetManifest(deps=None),
    #                     },
    #                 )
    #             ]
    #         ),
    #         group_name="group_a",
    #     )
    # )


defs = make_definitions_from_file_system()
assert make_definitions_from_python_api()


if __name__ == "__main__":
    assert isinstance(defs, Definitions)
