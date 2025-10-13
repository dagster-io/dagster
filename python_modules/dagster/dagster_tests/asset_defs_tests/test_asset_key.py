import dagster as dg
import pytest
from dagster import AssetKey
from dagster._core.definitions.asset_key import key_prefix_from_coercible


def test_key_prefix_from_coercible():
    assert key_prefix_from_coercible("foo") == ["foo"]
    assert key_prefix_from_coercible(["foo"]) == ["foo"]
    assert key_prefix_from_coercible(("foo",)) == ("foo",)


# While it's not trivial to achieve, slashes can ponentially sneak into asset keys
# inside definitions. These tests pin the current behavior around getting forward
# slashes into assets. We may want to forbid this in the future


def test_forward_slashes_fail():
    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.asset(key="foo/bar")
        def fn(): ...

    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.asset(key=["foo/bar"])
        def fn(): ...

    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.asset(key=["foo/bar", "baz"])
        def fn(): ...

    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.asset(key_prefix="foo/bar")
        def fn(): ...

    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.asset(key_prefix=["foo/bar"])
        def fn(): ...

    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.asset(key_prefix=["foo/bar", "baz"])
        def fn(): ...


@dg.asset(key=["baz"])
def asset_1(): ...


@dg.asset(key=["baz", "quix"])
def asset_2(): ...


source_asset = dg.SourceAsset(key=["key0"])


def test_forward_slashes_allowed():
    keys1 = [a.key for a in dg.load_assets_from_current_module(key_prefix="foo/bar")]  # pyright: ignore[reportAttributeAccessIssue]
    assert dg.AssetKey(["foo/bar", "baz"]) in keys1
    assert dg.AssetKey(["foo/bar", "baz", "quix"]) in keys1


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
