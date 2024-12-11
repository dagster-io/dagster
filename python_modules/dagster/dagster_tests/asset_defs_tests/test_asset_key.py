import pytest
from dagster import AssetKey, SourceAsset, asset, load_assets_from_current_module
from dagster._core.errors import DagsterInvalidDefinitionError

# While it's not trivial to achieve, slashes can ponentially sneak into asset keys
# inside definitions. These tests pin the current behavior around getting forward
# slashes into assets. We may want to forbid this in the future


def test_forward_slashes_fail():
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


def test_forward_slashes_allowed():
    keys1 = [a.key for a in load_assets_from_current_module(key_prefix="foo/bar")]  # pyright: ignore[reportAttributeAccessIssue]
    assert AssetKey(["foo/bar", "baz"]) in keys1
    assert AssetKey(["foo/bar", "baz", "quix"]) in keys1


def test_to_asset_key_path():
    assert AssetKey.from_escaped_user_string("foo").path == ["foo"]
    assert AssetKey.from_escaped_user_string("foo/bar").path == ["foo", "bar"]
    assert AssetKey.from_escaped_user_string(r"foo\/bar").path == ["foo/bar"]
    assert AssetKey.from_escaped_user_string("foo/bar/baz").path == [
        "foo",
        "bar",
        "baz",
    ]
    assert AssetKey.from_escaped_user_string(r"foo\/bar\/baz").path == ["foo/bar/baz"]
    assert AssetKey.from_escaped_user_string(r"foo\/bar/baz").path == ["foo/bar", "baz"]
    assert AssetKey.from_escaped_user_string(r"foo/bar\/baz").path == ["foo", "bar/baz"]
