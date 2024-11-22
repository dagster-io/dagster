from typing import Any, Dict

import pytest
from dagster import AssetKey, AssetsDefinition, asset
from dagster_dbt import get_asset_key_for_model, get_asset_keys_by_output_name_for_source
from dagster_dbt.asset_decorator import dbt_assets


@pytest.fixture(name="my_dbt_assets", scope="module")
def my_dbt_assets_fixture(test_meta_config_manifest: dict[str, Any]) -> AssetsDefinition:
    @dbt_assets(manifest=test_meta_config_manifest)
    def my_dbt_assets(): ...

    return my_dbt_assets


def test_asset_downstream_of_dbt_asset(my_dbt_assets: AssetsDefinition) -> None:
    upstream_asset_key = AssetKey(["orders"])

    @asset(deps=[get_asset_key_for_model([my_dbt_assets], "orders")])
    def downstream_python_asset(): ...

    assert upstream_asset_key in my_dbt_assets.keys_by_output_name.values()
    assert set(downstream_python_asset.keys_by_input_name.values()) == {upstream_asset_key}


def test_get_asset_keys_by_output_name_for_source(my_dbt_assets: AssetsDefinition) -> None:
    assert get_asset_keys_by_output_name_for_source([my_dbt_assets], "jaffle_shop") == {
        "source_test_dagster_meta_config_jaffle_shop_raw_customers": AssetKey(
            ["customized", "source", "jaffle_shop", "main", "raw_customers"]
        ),
        "source_test_dagster_meta_config_jaffle_shop_raw_events": AssetKey(
            ["jaffle_shop", "raw_events"]
        ),
    }

    with pytest.raises(KeyError, match="Could not find a dbt source with name"):
        get_asset_keys_by_output_name_for_source([my_dbt_assets], "nonexistent")


def test_get_asset_keys_for_model(my_dbt_assets: AssetsDefinition) -> None:
    assert get_asset_key_for_model([my_dbt_assets], "raw_customers") == AssetKey(["raw_customers"])
    assert get_asset_key_for_model([my_dbt_assets], "stg_customers") == AssetKey(
        ["customized", "staging", "customers"]
    )
    assert get_asset_key_for_model([my_dbt_assets], "customers") == AssetKey(["customers"])

    with pytest.raises(KeyError, match="Could not find a dbt model, seed, or snapshot with name"):
        get_asset_key_for_model([my_dbt_assets], "nonexistent")
