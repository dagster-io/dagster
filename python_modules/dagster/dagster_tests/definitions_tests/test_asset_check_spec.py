import re

import dagster as dg
import pytest


def test_coerce_asset_key():
    assert dg.AssetCheckSpec(asset="foo", name="check1").asset_key == dg.AssetKey("foo")


def test_asset_def():
    @dg.asset
    def foo(): ...

    assert dg.AssetCheckSpec(asset=foo, name="check1").asset_key == dg.AssetKey("foo")


def test_source_asset():
    foo = dg.SourceAsset("foo")

    assert dg.AssetCheckSpec(asset=foo, name="check1").asset_key == dg.AssetKey("foo")


def test_additional_deps():
    with pytest.raises(
        ValueError,
        match=re.escape(
            'Asset check check1 for asset ["foo"] cannot have an additional dependency on asset ["foo"].'
        ),
    ):
        dg.AssetCheckSpec(asset="foo", name="check1", additional_deps=["foo"])


def test_unserializable_metadata():
    class SomeObject: ...

    obj = SomeObject()

    assert (
        dg.AssetCheckSpec(asset="foo", name="check1", metadata={"foo": obj}).metadata["foo"] == obj
    )
