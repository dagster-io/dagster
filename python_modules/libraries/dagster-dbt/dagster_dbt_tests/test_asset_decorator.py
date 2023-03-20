from typing import AbstractSet, Optional

import pytest
from dagster import AssetKey, file_relative_path
from dagster._core.definitions.materialize import materialize
from dagster_dbt.asset_decorators import DbtExecutionContext, dbt_assets

from .utils import assert_assets_match_project


@pytest.mark.parametrize("prefix", [None, "foo", ["foo", "bar"]])
def test_structure(prefix) -> None:
    @dbt_assets(
        manifest_path=file_relative_path(__file__, "sample_manifest.json"),
        key_prefix=prefix,
    )
    def my_dbt_assets():
        ...

    assert_assets_match_project([my_dbt_assets], prefix=prefix)
