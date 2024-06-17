from typing import Any, Dict

import pytest
from dagster import AssetExecutionContext, AssetKey
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.asset_utils import generate_external_assets
from dagster_dbt.core.resources_v2 import DbtCliResource

pytest.importorskip("dbt.version", "1.6")


def test_dbt_external_assets_for_sources(
    test_external_source_assets_manifest: Dict[str, Any],
) -> None:
    @dbt_assets(manifest=test_external_source_assets_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    external_asset_defs = generate_external_assets([my_dbt_assets])[0]
    external_asset_keys = list(external_asset_defs.asset_and_check_keys)
    assert len(external_asset_keys) == 1
    assert external_asset_keys[0] == AssetKey(
        ["customized", "source", "jaffle_shop", "main", "raw_customers"]
    )
