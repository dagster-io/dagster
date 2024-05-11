from pathlib import Path

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions


def test_high_level_pydantic_parse() -> None:
    from examples.experimental.nope.nope_tutorial.high_level_dsl.high_level import (
        HighLevelDSLGroupFileManifest,
        load_yaml_to_pydantic,
    )

    yaml_manifest_path = Path(__file__).resolve().parent / Path(
        "defs/group_a.yaml"
    )

    manifest = load_yaml_to_pydantic(
        str(yaml_manifest_path.resolve()), HighLevelDSLGroupFileManifest
    )
    assert isinstance(manifest, HighLevelDSLGroupFileManifest)
    assert len(manifest.invocations) == 1
    invocation = next(iter(manifest.invocations))
    assert invocation.target == "bespoke_elt"
    assert invocation.name == "transform_and_load"
    assert invocation.source == "file://example/file.csv"
    assert invocation.destination == "s3://bucket/file.csv"
    assert len(invocation.assets) == 2

    assert set(invocation.assets.keys()) == {"root_one", "root_two"}
