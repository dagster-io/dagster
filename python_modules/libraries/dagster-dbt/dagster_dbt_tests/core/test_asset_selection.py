import os
from pathlib import Path
from typing import Any, Dict, Optional, Set

import pytest
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.internal_asset_graph import InternalAssetGraph
from dagster_dbt import build_dbt_asset_selection
from dagster_dbt.asset_decorator import dbt_assets


@pytest.mark.parametrize(
    ["select", "exclude", "expected_dbt_resource_names"],
    [
        (
            None,
            None,
            {
                "raw_customers",
                "raw_orders",
                "raw_payments",
                "stg_customers",
                "stg_orders",
                "stg_payments",
                "customers",
                "orders",
            },
        ),
        (
            "raw_customers stg_customers",
            None,
            {
                "raw_customers",
                "stg_customers",
            },
        ),
        (
            "raw_customers+",
            None,
            {
                "raw_customers",
                "stg_customers",
                "customers",
            },
        ),
        (
            "resource_type:model",
            None,
            {
                "stg_customers",
                "stg_orders",
                "stg_payments",
                "customers",
                "orders",
            },
        ),
        (
            "raw_customers+,resource_type:model",
            None,
            {
                "stg_customers",
                "customers",
            },
        ),
        (
            None,
            "orders",
            {
                "raw_customers",
                "raw_orders",
                "raw_payments",
                "stg_customers",
                "stg_orders",
                "stg_payments",
                "customers",
            },
        ),
        (
            None,
            "raw_customers+",
            {
                "raw_orders",
                "raw_payments",
                "stg_orders",
                "stg_payments",
                "orders",
            },
        ),
        (
            None,
            "raw_customers stg_customers",
            {
                "raw_orders",
                "raw_payments",
                "stg_orders",
                "stg_payments",
                "customers",
                "orders",
            },
        ),
        (
            None,
            "resource_type:model",
            {
                "raw_customers",
                "raw_orders",
                "raw_payments",
            },
        ),
        (
            None,
            "tag:does-not-exist",
            {
                "raw_customers",
                "raw_orders",
                "raw_payments",
                "stg_customers",
                "stg_orders",
                "stg_payments",
                "customers",
                "orders",
            },
        ),
    ],
    ids=[
        "--select fqn:*",
        "--select raw_customers stg_customers",
        "--select raw_customers+",
        "--select resource_type:model",
        "--select raw_customers+,resource_type:model",
        "--exclude orders",
        "--exclude raw_customers+",
        "--exclude raw_customers stg_customers",
        "--exclude resource_type:model",
        "--exclude tag:does-not-exist",
    ],
)
def test_dbt_asset_selection(
    test_jaffle_shop_manifest: Dict[str, Any],
    select: Optional[str],
    exclude: Optional[str],
    expected_dbt_resource_names: Set[str],
) -> None:
    expected_asset_keys = {AssetKey(key) for key in expected_dbt_resource_names}

    @dbt_assets(manifest=test_jaffle_shop_manifest)
    def my_dbt_assets():
        ...

    asset_graph = InternalAssetGraph.from_assets([my_dbt_assets])
    asset_selection = build_dbt_asset_selection(
        [my_dbt_assets],
        dbt_select=select or "fqn:*",
        dbt_exclude=exclude,
    )
    selected_asset_keys = asset_selection.resolve(all_assets=asset_graph)

    assert selected_asset_keys == expected_asset_keys


def test_dbt_asset_selection_manifest_argument(
    test_jaffle_shop_manifest_path: Path, test_jaffle_shop_manifest: Dict[str, Any]
) -> None:
    expected_asset_keys = {
        AssetKey(key)
        for key in {
            "raw_customers",
            "raw_orders",
            "raw_payments",
            "stg_customers",
            "stg_orders",
            "stg_payments",
            "customers",
            "orders",
        }
    }

    for manifest_param in [
        test_jaffle_shop_manifest,
        test_jaffle_shop_manifest_path,
        os.fspath(test_jaffle_shop_manifest_path),
    ]:

        @dbt_assets(manifest=manifest_param)
        def my_dbt_assets():
            ...

        asset_graph = InternalAssetGraph.from_assets([my_dbt_assets])
        asset_selection = build_dbt_asset_selection([my_dbt_assets], dbt_select="fqn:*")
        selected_asset_keys = asset_selection.resolve(all_assets=asset_graph)

        assert selected_asset_keys == expected_asset_keys
