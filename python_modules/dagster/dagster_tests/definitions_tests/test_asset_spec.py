import pytest
from dagster import AssetSpec
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.storage.tags import COMPUTE_KIND_TAG


def test_validate_asset_owner():
    with pytest.raises(DagsterInvalidDefinitionError, match="Invalid owner"):
        AssetSpec(key="asset1", owners=["owner@$#&*1"])


def test_compute_kind():
    asset_spec = AssetSpec(key="foo", compute_kind="bar")
    assert asset_spec.tags[COMPUTE_KIND_TAG] == "bar"
