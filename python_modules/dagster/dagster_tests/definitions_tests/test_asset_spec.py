import pytest
from dagster import AssetSpec
from dagster._core.errors import DagsterInvalidDefinitionError


def test_validate_asset_owner():
    with pytest.raises(DagsterInvalidDefinitionError, match="Invalid owner"):
        AssetSpec(key="asset1", owners=["owner@$#&*1"])
