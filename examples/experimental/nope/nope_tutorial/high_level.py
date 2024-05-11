from pathlib import Path
from typing import Dict, List, Optional

from dagster import _check as check
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.factory.executable import (
    AssetGraphExecutable,
    AssetGraphExecutionContext,
    AssetGraphExecutionResult,
)
from dagster._nope.definitions import (
    DefinitionsBuilder,
    InMemoryManifestSource,
    ManifestSource,
    make_nope_definitions,
)
from dagster._nope.parser import load_yaml_to_pydantic
from pydantic import BaseModel


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


class HighLevelDSLFileSystemManifestSource(ManifestSource):
    def __init__(self, path: Path):
        self.path = path

    @staticmethod
    def _get_single_yaml_file(path: Path) -> Path:
        yaml_files = {}
        for file_path in path.iterdir():
            # python_files = {}
            if file_path.suffix == ".yaml":
                yaml_files[file_path.stem] = file_path

        if len(yaml_files) != 1:
            raise Exception(f"Expected exactly one yaml file in {path}, found {yaml_files}")
        return next(iter(yaml_files.values()))

    def get_manifest(self) -> HighLevelDSLManifest:
        single_group_yaml_file = HighLevelDSLFileSystemManifestSource._get_single_yaml_file(
            self.path
        )
        group_file_manifest = check.inst(
            load_yaml_to_pydantic(str(single_group_yaml_file), HighLevelDSLGroupFileManifest),
            HighLevelDSLGroupFileManifest,
        )
        return HighLevelDSLManifest(group_name=self.path.stem, manifest_file=group_file_manifest)


class HighLevelDSLDefsBuilder(DefinitionsBuilder):
    @classmethod
    def build(cls, manifest: HighLevelDSLManifest) -> Definitions:
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


def make_definitions_from_python_api() -> Definitions:
    return make_nope_definitions(
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
        ),
        defs_builder_cls=HighLevelDSLDefsBuilder,
    )


defs = make_nope_definitions(
    manifest_source=HighLevelDSLFileSystemManifestSource(
        path=Path(__file__).resolve().parent / Path("high_level_defs")
    ),
    defs_builder_cls=HighLevelDSLDefsBuilder,
)


assert make_definitions_from_python_api()


if __name__ == "__main__":
    assert isinstance(defs, Definitions)
