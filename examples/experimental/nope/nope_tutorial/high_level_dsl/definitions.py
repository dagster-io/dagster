from pathlib import Path

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
    make_nope_definitions,
)
from manifest import (
    BespokeELTAssetManifest,
    BespokeELTInvocationTargetManifest,
    HighLevelDSLGroupFileManifest,
    HighLevelDSLManifest,
)
from manifest_source import HighLevelDSLFileSystemManifestSource


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
        path=Path(__file__).resolve().parent / Path("defs")
    ),
    defs_builder_cls=HighLevelDSLDefsBuilder,
)


assert make_definitions_from_python_api()


if __name__ == "__main__":
    assert isinstance(defs, Definitions)
