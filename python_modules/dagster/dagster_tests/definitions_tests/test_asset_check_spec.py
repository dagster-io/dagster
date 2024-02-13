import re

import pytest
from dagster import AssetCheckSpec, AssetKey, SourceAsset, asset


def test_coerce_asset_key():
    assert AssetCheckSpec(asset="foo", name="check1").asset_key == AssetKey("foo")


def test_asset_def():
    @asset
    def foo():
        ...

    assert AssetCheckSpec(asset=foo, name="check1").asset_key == AssetKey("foo")


def test_source_asset():
    foo = SourceAsset("foo")

    assert AssetCheckSpec(asset=foo, name="check1").asset_key == AssetKey("foo")


def test_additional_deps():
    with pytest.raises(
        ValueError,
        match=re.escape(
            'Asset check check1 for asset ["foo"] cannot have an additional dependency on asset ["foo"].'
        ),
    ):
        AssetCheckSpec(asset="foo", name="check1", additional_deps=["foo"])
