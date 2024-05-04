from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dagster import _check as check
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.definitions_class import Definitions
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


class HighLevelDSLManifestFile(BaseModel):
    invocations: List[BespokeELTInvocationTargetManifest]


class HighLevelDSLManifest(BaseModel):
    group_name: str

    manifest_file: HighLevelDSLManifestFile

    def to_definitions(self) -> Definitions:
        assets_defs = []
        for invocation in self.manifest_file.invocations:

            @multi_asset(
                name=invocation.name,
                specs=[AssetSpec(key=asset_key) for asset_key in invocation.assets.keys()],
                group_name=self.group_name,
            )
            def _asset() -> Any: ...

            assets_defs.append(_asset)
        return Definitions(assets_defs)


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
        return HighLevelDSLManifest(
            group_name=group_manifest_path.stem,
            manifest_file=check.inst(
                load_yaml_to_pydantic(str(group_manifest_path.resolve()), HighLevelDSLManifestFile),
                HighLevelDSLManifestFile,
            ),
        ).to_definitions()


def make_definitions_from_group_manifest(
    group_manifest: HighLevelDSLManifestFile, group_name: str
) -> Definitions:
    assert isinstance(group_manifest, HighLevelDSLManifestFile)
    assets_defs = []
    for invocation in group_manifest.invocations:

        @multi_asset(
            name=invocation.name,
            specs=[AssetSpec(key=asset_key) for asset_key in invocation.assets.keys()],
            group_name=group_name,
        )
        def _asset() -> Any: ...

        assets_defs.append(_asset)
    return Definitions(assets_defs)


def make_definitions_from_file_system() -> Definitions:
    return HighLevelDSLNopeProject.make_definitions(
        defs_path=Path(__file__).resolve().parent / Path("high_level_defs")
    )


def make_definitions_from_python_api() -> Definitions:
    return HighLevelDSLManifest(
        manifest_file=HighLevelDSLManifestFile(
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
        group_name="group_a",
    ).to_definitions()


defs = make_definitions_from_file_system()


if __name__ == "__main__":
    assert isinstance(defs, Definitions)
