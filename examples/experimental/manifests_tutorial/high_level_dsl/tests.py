from pathlib import Path

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._manifest.pydantic_yaml import load_yaml_to_pydantic
from definitions import HighLevelDSLManifestFactory, make_high_level_dsl_definitions
from executables.bespoke_elt import (
    BespokeELTAssetManifest,
    BespokeELTExecutableManifest,
)
from manifest import (
    HighLevelDSLManifest,
)


def test_high_level_pydantic_parse() -> None:
    from examples.experimental.manifests_tutorial.high_level_dsl.manifest import (
        HighLevelDSLManifest,
    )

    yaml_manifest_path = Path(__file__).resolve().parent / Path("manifests/group_a.yaml")

    manifest = load_yaml_to_pydantic(str(yaml_manifest_path.resolve()), HighLevelDSLManifest)
    assert isinstance(manifest, HighLevelDSLManifest)
    assert len(manifest.executables) == 3
    invocation = next(iter(manifest.executables))
    assert invocation.kind == "bespoke_elt"
    assert invocation.name == "transform_and_load"
    assert invocation.source == "file://example/file.csv"
    assert invocation.destination == "s3://bucket/file.csv"
    assert len(invocation.assets) == 2

    assert {asset.key for asset in invocation.assets} == {"root_one", "root_two"}


def test_demonstrate_building_from_manifests() -> None:
    def make_definitions_from_python_api() -> Definitions:
        manifest = HighLevelDSLManifest(
            executables=[
                BespokeELTExecutableManifest(
                    name="transform_and_load",
                    kind="bespoke_elt",
                    group_name="group_a",
                    source="file://example/file.csv",
                    destination="s3://bucket/file.csv",
                    assets=[
                        BespokeELTAssetManifest(key="root_one"),
                        BespokeELTAssetManifest(key="root_two"),
                    ],
                )
            ]
        )
        return HighLevelDSLManifestFactory().make_definitions(
            manifest=manifest,
            resources={},
        )

    assert isinstance(make_definitions_from_python_api(), Definitions)


def test_dbt_assets() -> None:
    defs = make_high_level_dsl_definitions()
    assets_def = defs.get_assets_def("raw_customers")
    assert isinstance(assets_def, AssetsDefinition)


def test_subprocess_assets() -> None:
    defs = make_high_level_dsl_definitions()
    assert isinstance(
        defs.get_assets_def(AssetKey.from_user_string("ml_team/downstream")), AssetsDefinition
    )
