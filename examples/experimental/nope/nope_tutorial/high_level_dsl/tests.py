from pathlib import Path

from dagster._nope.parser import load_yaml_to_pydantic


def test_high_level_pydantic_parse() -> None:
    from examples.experimental.nope.nope_tutorial.high_level_dsl.definitions import (
        HighLevelDSLExecutableList,
    )

    yaml_manifest_path = Path(__file__).resolve().parent / Path("defs/group_a.high_level.yaml")

    manifest = load_yaml_to_pydantic(str(yaml_manifest_path.resolve()), HighLevelDSLExecutableList)
    assert isinstance(manifest, HighLevelDSLExecutableList)
    assert len(manifest.executables) == 2
    invocation = next(iter(manifest.executables))
    assert invocation.kind == "bespoke_elt"
    assert invocation.name == "transform_and_load"
    assert invocation.source == "file://example/file.csv"
    assert invocation.destination == "s3://bucket/file.csv"
    assert len(invocation.assets) == 2

    assert set(invocation.assets.keys()) == {"root_one", "root_two"}
