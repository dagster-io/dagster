from typing import TYPE_CHECKING, Any

import pytest
from dagster import AssetKey
from dagster_dbt import build_dbt_asset_specs, dbt_assets
from dagster_dbt.asset_utils import default_asset_key_fn

if TYPE_CHECKING:
    from collections.abc import Mapping


def test_default_asset_key_fn_asset_key_takes_precedence_over_prefix() -> None:
    dbt_resource_props: Mapping[str, Any] = {
        "name": "orders",
        "resource_type": "model",
        "config": {
            "meta": {
                "dagster": {
                    "asset_key": ["warehouse", "jaffle_shop", "orders"],
                    "asset_key_prefix": ["ignored", "prefix"],
                }
            }
        },
    }

    assert default_asset_key_fn(dbt_resource_props) == AssetKey(
        ["warehouse", "jaffle_shop", "orders"]
    )


@pytest.mark.parametrize(
    "resource_type,name",
    [
        ("model", "orders"),
        ("snapshot", "orders_snapshot"),
    ],
)
def test_default_asset_key_fn_asset_key_prefix_for_supported_resource_types(
    resource_type: str, name: str
) -> None:
    dbt_resource_props = {
        "name": name,
        "resource_type": resource_type,
        "source_name": "jaffle_shop",
        "config": {"meta": {"dagster": {"asset_key_prefix": ["snowflake", "jaffle_shop"]}}},
    }

    assert default_asset_key_fn(dbt_resource_props) == AssetKey(["snowflake", "jaffle_shop", name])


def test_default_asset_key_fn_asset_key_prefix_for_source() -> None:
    # For sources, the key is: prefix + source_name + table_name
    dbt_resource_props = {
        "name": "raw_orders",
        "resource_type": "source",
        "source_name": "jaffle_shop",
        "config": {"meta": {"dagster": {"asset_key_prefix": ["snowflake"]}}},
    }

    assert default_asset_key_fn(dbt_resource_props) == AssetKey(
        ["snowflake", "jaffle_shop", "raw_orders"]
    )


def test_default_asset_key_fn_asset_key_prefix_uses_alias_for_versioned_models() -> None:
    dbt_resource_props = {
        "name": "orders",
        "alias": "orders_v1",
        "version": 1,
        "resource_type": "model",
        "config": {"meta": {"dagster": {"asset_key_prefix": ["snowflake", "jaffle_shop"]}}},
    }

    assert default_asset_key_fn(dbt_resource_props) == AssetKey(
        ["snowflake", "jaffle_shop", "orders_v1"]
    )


def test_default_asset_key_fn_asset_key_prefix_from_meta_path() -> None:
    # Sources read asset_key_prefix from top-level meta, not config.meta
    dbt_resource_props = {
        "name": "orders",
        "resource_type": "source",
        "source_name": "jaffle_shop",
        "config": {},
        "meta": {"dagster": {"asset_key_prefix": ["raw"]}},
    }

    assert default_asset_key_fn(dbt_resource_props) == AssetKey(["raw", "jaffle_shop", "orders"])


def test_default_asset_key_fn_empty_asset_key_prefix_uses_node_name() -> None:
    dbt_resource_props = {
        "name": "orders",
        "resource_type": "model",
        "config": {"meta": {"dagster": {"asset_key_prefix": []}}},
    }

    assert default_asset_key_fn(dbt_resource_props) == AssetKey(["orders"])


def test_default_asset_key_fn_asset_key_prefix_accepts_string() -> None:
    dbt_resource_props = {
        "name": "orders",
        "resource_type": "model",
        "config": {"meta": {"dagster": {"asset_key_prefix": "snowflake"}}},
    }

    assert default_asset_key_fn(dbt_resource_props) == AssetKey(["snowflake", "orders"])


def test_default_asset_key_fn_asset_key_prefix_with_schema() -> None:
    # When both prefix and schema are configured, schema is appended after prefix
    dbt_resource_props = {
        "name": "orders",
        "resource_type": "model",
        "config": {
            "schema": "analytics",
            "meta": {"dagster": {"asset_key_prefix": ["snowflake"]}},
        },
    }

    assert default_asset_key_fn(dbt_resource_props) == AssetKey(
        ["snowflake", "analytics", "orders"]
    )


def test_dbt_meta_asset_key_prefix_with_inherited_config(
    test_asset_key_prefix_manifest: dict[str, Any],
) -> None:
    expected_specs_by_key = {
        spec.key: spec for spec in build_dbt_asset_specs(manifest=test_asset_key_prefix_manifest)
    }

    @dbt_assets(manifest=test_asset_key_prefix_manifest)
    def my_dbt_assets(): ...

    assert AssetKey(["warehouse", "jaffle_shop", "orders_from_source"]) in my_dbt_assets.keys
    assert AssetKey(["override", "explicit_asset_key"]) in my_dbt_assets.keys
    assert AssetKey(["warehouse", "jaffle_shop", "explicit_asset_key"]) not in my_dbt_assets.keys

    assert AssetKey(["staging", "raw", "orders"]) in set(my_dbt_assets.keys_by_input_name.values())

    assert AssetKey(["warehouse", "jaffle_shop", "orders_from_source"]) in expected_specs_by_key
    assert AssetKey(["override", "explicit_asset_key"]) in expected_specs_by_key
