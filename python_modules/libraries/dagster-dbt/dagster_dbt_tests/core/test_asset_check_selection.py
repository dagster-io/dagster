from typing import Any, Dict

import pytest
from dagster import AssetCheckKey, AssetKey, AssetsDefinition
from dagster._core.definitions.internal_asset_graph import InternalAssetGraph
from dagster_dbt import (
    DagsterDbtTranslator,
    DagsterDbtTranslatorSettings,
    build_dbt_asset_selection,
)
from dagster_dbt.asset_decorator import dbt_assets

dagster_dbt_translator_with_checks = DagsterDbtTranslator(
    settings=DagsterDbtTranslatorSettings(enable_asset_checks=True)
)


@pytest.fixture(name="my_dbt_assets", scope="module")
def my_dbt_assets_fixture(test_asset_checks_manifest: Dict[str, Any]) -> AssetsDefinition:
    @dbt_assets(
        manifest=test_asset_checks_manifest,
        dagster_dbt_translator=dagster_dbt_translator_with_checks,
    )
    def my_dbt_assets():
        ...

    return my_dbt_assets


@pytest.fixture(name="asset_graph", scope="module")
def asset_graph_fixture(my_dbt_assets: AssetsDefinition) -> InternalAssetGraph:
    return InternalAssetGraph.from_assets([my_dbt_assets])


ALL_ASSET_KEYS = {
    AssetKey([key])
    for key in [
        "customers",
        "orders",
        "raw_customers",
        "raw_orders",
        "raw_payments",
        "stg_customers",
        "stg_orders",
        "stg_payments",
        "raw_fail_tests_model",
        "fail_tests_model",
    ]
}


ALL_CHECK_KEYS = {
    AssetCheckKey(asset_key=AssetKey([asset_name]), name=check_name)
    for asset_name, check_name in [
        ("customers", "not_null_customers_customer_id"),
        ("customers", "unique_customers_customer_id"),
        (
            "orders",
            "accepted_values_orders_status__placed__shipped__completed__return_pending__returned",
        ),
        ("orders", "not_null_orders_amount"),
        ("orders", "not_null_orders_bank_transfer_amount"),
        ("orders", "not_null_orders_coupon_amount"),
        ("orders", "not_null_orders_credit_card_amount"),
        ("orders", "not_null_orders_customer_id"),
        ("orders", "not_null_orders_gift_card_amount"),
        ("orders", "not_null_orders_order_id"),
        ("orders", "relationships_orders_customer_id__customer_id__ref_customers_"),
        (
            "orders",
            "relationships_with_duplicate_orders_ref_customers___customer_id__customer_id__ref_customers_",
        ),
        ("orders", "unique_orders_order_id"),
        ("stg_customers", "not_null_stg_customers_customer_id"),
        ("stg_customers", "unique_stg_customers_customer_id"),
        (
            "stg_orders",
            "accepted_values_stg_orders_status__placed__shipped__completed__return_pending__returned",
        ),
        ("stg_orders", "not_null_stg_orders_order_id"),
        ("stg_orders", "unique_stg_orders_order_id"),
        (
            "stg_payments",
            "accepted_values_stg_payments_payment_method__credit_card__coupon__bank_transfer__gift_card",
        ),
        ("stg_payments", "not_null_stg_payments_payment_id"),
        ("stg_payments", "unique_stg_payments_payment_id"),
        ("fail_tests_model", "accepted_values_fail_tests_model_first_name__foo__bar__baz"),
        ("fail_tests_model", "unique_fail_tests_model_id"),
        (
            "orders",
            "relationships_orders_customer_id__customer_id__source_jaffle_shop_raw_customers_",
        ),
    ]
}


def test_all(my_dbt_assets: AssetsDefinition, asset_graph: InternalAssetGraph) -> None:
    asset_selection = build_dbt_asset_selection([my_dbt_assets], dbt_select="fqn:*")
    assert asset_selection.resolve(asset_graph) == ALL_ASSET_KEYS
    assert asset_selection.resolve_checks(asset_graph) == ALL_CHECK_KEYS


def test_tag(my_dbt_assets: AssetsDefinition, asset_graph: InternalAssetGraph) -> None:
    asset_selection = build_dbt_asset_selection([my_dbt_assets], dbt_select="tag:data_quality")
    assert asset_selection.resolve(asset_graph) == set()
    assert asset_selection.resolve_checks(asset_graph) == {
        AssetCheckKey(asset_key=AssetKey(["customers"]), name="unique_customers_customer_id")
    }

    asset_selection = build_dbt_asset_selection([my_dbt_assets], dbt_exclude="tag:data_quality")
    assert asset_selection.resolve(asset_graph) == ALL_ASSET_KEYS
    assert asset_selection.resolve_checks(asset_graph) == ALL_CHECK_KEYS - {
        AssetCheckKey(asset_key=AssetKey(["customers"]), name="unique_customers_customer_id")
    }


def test_selection_customers(
    my_dbt_assets: AssetsDefinition, asset_graph: InternalAssetGraph
) -> None:
    asset_selection = build_dbt_asset_selection([my_dbt_assets], dbt_select="customers")
    assert asset_selection.resolve(asset_graph) == {AssetKey(["customers"])}
    # all tests that reference model customers- includes a relationship test on orders
    assert asset_selection.resolve_checks(asset_graph) == {
        key for key in ALL_CHECK_KEYS if key.asset_key == AssetKey(["customers"])
    } | {
        AssetCheckKey(
            asset_key=AssetKey(["orders"]),
            name="relationships_orders_customer_id__customer_id__ref_customers_",
        ),
        AssetCheckKey(
            asset_key=AssetKey(["orders"]),
            name="relationships_with_duplicate_orders_ref_customers___customer_id__customer_id__ref_customers_",
        ),
    }


def test_excluding_tests(my_dbt_assets: AssetsDefinition, asset_graph: InternalAssetGraph) -> None:
    asset_selection = build_dbt_asset_selection(
        [my_dbt_assets],
        dbt_select="customers",
        dbt_exclude=" ".join(
            [
                "not_null_customers_customer_id",
                "unique_customers_customer_id",
                "relationships_orders_customer_id__customer_id__ref_customers_",
                "relationships_with_duplicate_orders_ref_customers___customer_id__customer_id__ref_customers_",
            ]
        ),
    )
    assert asset_selection.resolve(asset_graph) == {AssetKey(["customers"])}
    assert asset_selection.resolve_checks(asset_graph) == set()
