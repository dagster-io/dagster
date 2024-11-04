import pytest
from dagster import AssetKey, AssetSpec, SourceAsset, asset, load_assets_from_current_module
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.errors import DagsterInvalidDefinitionError


def test_forward_slashes_in_keys_fail():
    with pytest.raises(DagsterInvalidDefinitionError):

        @asset(key="foo/bar")
        def fn(): ...

    with pytest.raises(DagsterInvalidDefinitionError):

        @asset(key=["foo/bar"])
        def fn(): ...

    with pytest.raises(DagsterInvalidDefinitionError):

        @asset(key=["foo/bar", "baz"])
        def fn(): ...

    with pytest.raises(DagsterInvalidDefinitionError):

        @asset(key_prefix="foo/bar")
        def fn(): ...

    with pytest.raises(DagsterInvalidDefinitionError):

        @asset(key_prefix=["foo/bar"])
        def fn(): ...

    with pytest.raises(DagsterInvalidDefinitionError):

        @asset(key_prefix=["foo/bar", "baz"])
        def fn(): ...


@asset(key=["baz"])
def asset_1(): ...


@asset(key=["baz", "quix"])
def asset_2(): ...


source_asset = SourceAsset(key=["key0"])


def test_forward_slashes_in_keys_allowed():
    keys1 = [a.key for a in load_assets_from_current_module(key_prefix="foo/bar")]
    assert AssetKey(["foo/bar", "baz"]) in keys1
    assert AssetKey(["foo/bar", "baz", "quix"]) in keys1
    assert AssetKey(["foo/bar", "baz", "quix"]) in keys1

    keys2 = [a.key for a in load_assets_from_current_module(key_prefix=["foo/bar"])]
    assert AssetKey(["foo/bar", "baz"]) in keys2
    assert AssetKey(["foo/bar", "baz", "quix"]) in keys2
    assert AssetKey(["foo/bar", "baz", "quix"]) in keys2

    AssetsDefinition(specs=[AssetSpec("foo/bar")])
    AssetsDefinition(specs=[AssetSpec(["foo/bar"])])
