from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Optional

import pytest
from dagster import AssetKey, AssetSpec, Definitions
from dagster_looker.lkml.asset_specs import build_looker_asset_specs
from dagster_looker.lkml.dagster_looker_lkml_translator import (
    DagsterLookerLkmlTranslator,
    LookMLStructureType,
)

from dagster_looker_tests.looker_projects import (
    test_exception_derived_table_path,
    test_extensions,
    test_liquid_path,
    test_refinements,
    test_retail_demo_path,
    test_union_no_distinct_path,
)


def test_build_looker_asset_specs_as_external_assets() -> None:
    looker_specs = build_looker_asset_specs(project_dir=test_retail_demo_path)

    Definitions.validate_loadable(Definitions(assets=looker_specs))


def test_asset_deps() -> None:
    my_looker_assets = build_looker_asset_specs(project_dir=test_retail_demo_path)
    asset_deps = {}
    for spec in my_looker_assets:
        asset_deps[spec.key] = {dep.asset_key for dep in spec.deps}

    assert asset_deps == {
        # Dashboards
        AssetKey(["dashboard", "address_deepdive"]): {
            AssetKey(["explore", "transactions"]),
        },
        AssetKey(["dashboard", "campaign_activation"]): {
            AssetKey(["explore", "omni_channel_transactions"])
        },
        AssetKey(["dashboard", "customer_360"]): {
            AssetKey(["explore", "omni_channel_events"]),
            AssetKey(["explore", "omni_channel_transactions"]),
        },
        AssetKey(["dashboard", "customer_deep_dive"]): {
            AssetKey(["explore", "customer_transaction_fact"]),
            AssetKey(["explore", "omni_channel_transactions"]),
        },
        AssetKey(["dashboard", "customer_segment_deepdive"]): {
            AssetKey(["explore", "transactions"])
        },
        AssetKey(["dashboard", "group_overview"]): {
            AssetKey(["explore", "transactions"]),
        },
        AssetKey(["dashboard", "item_affinity_analysis"]): {
            AssetKey(["explore", "order_purchase_affinity"])
        },
        AssetKey(["dashboard", "store_deepdive"]): {
            AssetKey(["explore", "stock_forecasting_explore_base"]),
            AssetKey(["explore", "transactions"]),
        },
        # Explores
        AssetKey(["explore", "customer_clustering_prediction"]): {
            AssetKey(["view", "customer_clustering_prediction"]),
            AssetKey(["view", "transactions"]),
        },
        AssetKey(["explore", "customer_event_fact"]): {AssetKey(["view", "customer_event_fact"])},
        AssetKey(["explore", "customer_transaction_fact"]): {
            AssetKey(["view", "customer_event_fact"]),
            AssetKey(["view", "customer_support_fact"]),
            AssetKey(["view", "customer_transaction_fact"]),
        },
        AssetKey(["explore", "omni_channel_events"]): {
            AssetKey(["view", "c360"]),
            AssetKey(["view", "omni_channel_events"]),
            AssetKey(["view", "omni_channel_transactions"]),
            AssetKey(["view", "omni_channel_transactions__transaction_details"]),
            AssetKey(["view", "retail_clv_predict"]),
        },
        AssetKey(["explore", "omni_channel_support_calls"]): {
            AssetKey(["view", "omni_channel_support_calls"]),
        },
        AssetKey(["explore", "omni_channel_transactions"]): {
            AssetKey(["view", "c360"]),
            AssetKey(["view", "customers"]),
            AssetKey(["view", "omni_channel_transactions"]),
            AssetKey(["view", "omni_channel_transactions__transaction_details"]),
            AssetKey(["view", "retail_clv_predict"]),
        },
        AssetKey(["explore", "order_purchase_affinity"]): {
            AssetKey(["view", "order_items_base"]),
            AssetKey(["view", "order_purchase_affinity"]),
            AssetKey(["view", "total_orders"]),
        },
        AssetKey(["explore", "stock_forecasting_explore_base"]): {
            AssetKey(["view", "stock_forecasting_explore_base"]),
            AssetKey(["view", "stock_forecasting_prediction"]),
        },
        AssetKey(["explore", "transactions"]): {
            AssetKey(["view", "channels"]),
            AssetKey(["view", "customer_clustering_prediction"]),
            AssetKey(["view", "customer_facts"]),
            AssetKey(["view", "customer_transaction_sequence"]),
            AssetKey(["view", "customers"]),
            AssetKey(["view", "products"]),
            AssetKey(["view", "store_weather"]),
            AssetKey(["view", "stores"]),
            AssetKey(["view", "transactions"]),
            AssetKey(["view", "transactions__line_items"]),
        },
        # Views
        AssetKey(["view", "c360"]): {
            AssetKey(["c360"]),
        },
        AssetKey(["view", "category_lookup"]): {
            AssetKey(["looker-private-demo", "retail", "category_lookup"])
        },
        AssetKey(["view", "channels"]): {
            AssetKey(["looker-private-demo", "retail", "channels"]),
        },
        AssetKey(["view", "customer_clustering_input"]): {
            AssetKey(["customer_clustering_input"]),
        },
        AssetKey(["view", "customer_clustering_model"]): {
            AssetKey(["customer_clustering_model"]),
        },
        AssetKey(["view", "customer_clustering_prediction"]): {
            AssetKey(["view", "customer_clustering_prediction_base"]),
            AssetKey(["view", "customer_clustering_prediction_centroid_ranks"]),
        },
        AssetKey(["view", "customer_clustering_prediction_aggregates"]): {
            AssetKey(["view", "customer_clustering_prediction_base"])
        },
        AssetKey(["view", "customer_clustering_prediction_base"]): {
            AssetKey(["view", "customer_clustering_input"]),
            AssetKey(["view", "customer_clustering_model"]),
        },
        AssetKey(["view", "customer_clustering_prediction_centroid_ranks"]): {
            AssetKey(["view", "customer_clustering_prediction_aggregates"])
        },
        AssetKey(["view", "customer_event_fact"]): {
            AssetKey(["customer_event_fact"]),
        },
        AssetKey(["view", "customer_facts"]): {
            AssetKey(["view", "transactions"]),
        },
        AssetKey(["view", "customer_support_fact"]): {
            AssetKey(["customer_support_fact"]),
        },
        AssetKey(["view", "customer_transaction_fact"]): {
            AssetKey(["customer_transaction_fact"]),
        },
        AssetKey(["view", "customer_transaction_sequence"]): {
            AssetKey(["view", "products"]),
            AssetKey(["view", "transactions"]),
        },
        AssetKey(["view", "customers"]): {
            AssetKey(["looker-private-demo", "retail", "customers"]),
        },
        AssetKey(["view", "date_comparison"]): {
            AssetKey(["date_comparison"]),
        },
        AssetKey(["view", "distances"]): {
            AssetKey(["view", "stores"]),
        },
        AssetKey(["view", "events"]): {
            AssetKey(["looker-private-demo", "retail", "events"]),
        },
        AssetKey(["view", "omni_channel_events"]): {
            AssetKey(["looker-private-demo", "ecomm", "events"])
        },
        AssetKey(["view", "omni_channel_support_calls"]): {
            AssetKey(["looker-private-demo", "call_center", "transcript_with_messages"])
        },
        AssetKey(["view", "omni_channel_support_calls__messages"]): {
            AssetKey(["omni_channel_support_calls__messages"])
        },
        AssetKey(["view", "omni_channel_transactions"]): {
            AssetKey(["looker-private-demo", "ecomm", "inventory_items"]),
            AssetKey(["looker-private-demo", "ecomm", "order_items"]),
            AssetKey(["looker-private-demo", "ecomm", "products"]),
            AssetKey(["looker-private-demo", "ecomm", "users"]),
            AssetKey(["looker-private-demo", "retail", "channels"]),
            AssetKey(["looker-private-demo", "retail", "products"]),
            AssetKey(["looker-private-demo", "retail", "transaction_detail"]),
            AssetKey(["looker-private-demo", "retail", "us_stores"]),
        },
        AssetKey(["view", "omni_channel_transactions__transaction_details"]): {
            AssetKey(["omni_channel_transactions__transaction_details"])
        },
        AssetKey(["view", "order_items"]): {
            AssetKey(["view", "order_items_base"]),
        },
        AssetKey(["view", "order_items_base"]): {
            AssetKey(["view", "products"]),
            AssetKey(["view", "stores"]),
            AssetKey(["view", "transactions"]),
        },
        AssetKey(["view", "order_metrics"]): {
            AssetKey(["view", "order_items"]),
        },
        AssetKey(["view", "order_product"]): {
            AssetKey(["view", "order_items"]),
            AssetKey(["view", "orders"]),
        },
        AssetKey(["view", "order_purchase_affinity"]): {
            AssetKey(["view", "order_product"]),
            AssetKey(["view", "orders_by_product_loyal_users"]),
            AssetKey(["view", "total_order_product"]),
        },
        AssetKey(["view", "orders"]): {
            AssetKey(["view", "order_items"]),
        },
        AssetKey(["view", "orders_by_product_loyal_users"]): {
            AssetKey(["view", "order_items"]),
            AssetKey(["view", "product_loyal_users"]),
        },
        AssetKey(["view", "product_loyal_users"]): {
            AssetKey(["view", "order_items"]),
        },
        AssetKey(["view", "products"]): {
            AssetKey(["looker-private-demo", "retail", "products"]),
        },
        AssetKey(["view", "retail_clv_predict"]): {
            AssetKey(["retail_ltv", "lpd_retail_clv_predict_tbl"])
        },
        AssetKey(["view", "stock_forecasting_category_week_facts_prior_year"]): {
            AssetKey(["stock_forecasting_category_week_facts_prior_year"])
        },
        AssetKey(["view", "stock_forecasting_explore_base"]): {
            AssetKey(["stock_forecasting_explore_base"])
        },
        AssetKey(["view", "stock_forecasting_input"]): {
            AssetKey(["stock_forecasting_input"]),
        },
        AssetKey(["view", "stock_forecasting_prediction"]): {
            AssetKey(["view", "stock_forecasting_input"]),
            AssetKey(["view", "stock_forecasting_regression"]),
        },
        AssetKey(["view", "stock_forecasting_product_store_week_facts"]): {
            AssetKey(["stock_forecasting_product_store_week_facts"])
        },
        AssetKey(["view", "stock_forecasting_product_store_week_facts_prior_year"]): {
            AssetKey(["stock_forecasting_product_store_week_facts_prior_year"])
        },
        AssetKey(["view", "stock_forecasting_regression"]): {
            AssetKey(["stock_forecasting_regression"])
        },
        AssetKey(["view", "stock_forecasting_store_week_facts_prior_year"]): {
            AssetKey(["stock_forecasting_store_week_facts_prior_year"])
        },
        AssetKey(["view", "store_weather"]): {
            AssetKey(["view", "distances"]),
            AssetKey(["view", "weather_pivoted"]),
        },
        AssetKey(["view", "stores"]): {
            AssetKey(["view", "transactions"]),
        },
        AssetKey(["view", "total_order_product"]): {
            AssetKey(["view", "order_items"]),
            AssetKey(["view", "order_metrics"]),
            AssetKey(["view", "orders"]),
        },
        AssetKey(["view", "total_orders"]): {
            AssetKey(["view", "orders"]),
        },
        AssetKey(["view", "transaction_detail"]): {
            AssetKey(["transaction_detail"]),
        },
        AssetKey(["view", "transactions"]): {
            AssetKey(["looker-private-demo", "retail", "transaction_detail"])
        },
        AssetKey(["view", "transactions__line_items"]): {
            AssetKey(["transactions__line_items"]),
        },
        AssetKey(["view", "weather_pivoted"]): {
            AssetKey(["view", "weather_raw"]),
        },
        AssetKey(["view", "weather_raw"]): {
            AssetKey(["bigquery-public-data", "ghcn_d", "ghcnd_2016"]),
            AssetKey(["bigquery-public-data", "ghcn_d", "ghcnd_2017"]),
            AssetKey(["bigquery-public-data", "ghcn_d", "ghcnd_2018"]),
            AssetKey(["bigquery-public-data", "ghcn_d", "ghcnd_2019"]),
            AssetKey(["bigquery-public-data", "ghcn_d", "ghcnd_202_star"]),
        },
    }


def test_asset_deps_exception_derived_table(caplog: pytest.LogCaptureFixture) -> None:
    [spec] = build_looker_asset_specs(project_dir=test_exception_derived_table_path)

    assert spec.key == AssetKey(["view", "exception_derived_table"])
    assert not spec.deps
    assert (
        "Failed to parse derived table SQL for view `exception_derived_table`"
        " in file `exception_derived_table.view.lkml`."
        " The upstream dependencies for the view will be omitted."
    ) in caplog.text


def test_union_no_distinct_table(caplog: pytest.LogCaptureFixture) -> None:
    [spec] = build_looker_asset_specs(project_dir=test_union_no_distinct_path)

    assert spec.key == AssetKey(["view", "union_table"])
    # Ensure we parse out the union correctly
    assert len(list(spec.deps)) == 2


def test_liquid(caplog: pytest.LogCaptureFixture) -> None:
    [spec] = build_looker_asset_specs(project_dir=test_liquid_path)

    assert spec.key == AssetKey(["view", "liquid_derived_table"])
    # assert not spec.deps
    assert (
        "SQL for view `liquid_derived_table`"
        " in file `liquid_derived_table.view.lkml`"
        " contains Liquid variables or conditions. Upstream dependencies are parsed as best-effort."
    ) in caplog.text
    assert {dep.asset_key for dep in spec.deps} == {
        AssetKey(["looker-private-demo", "retail", "us_stores"]),
    }


def test_refinement_views(caplog: pytest.LogCaptureFixture):
    [spec] = build_looker_asset_specs(project_dir=test_refinements)

    assert spec.key == AssetKey(["view", "base"])
    assert len(list(spec.deps)) == 1

    # Ensure we get the asset key from the refined view
    assert next(iter(spec.deps)).asset_key == AssetKey(["prod", "new_base_data"])


def test_extension_views(caplog: pytest.LogCaptureFixture):
    specs = build_looker_asset_specs(project_dir=test_extensions)

    assert len(specs) == 3
    assert set(spec.key for spec in specs) == {
        AssetKey(["view", "base"]),
        AssetKey(["view", "extension"]),
        AssetKey(["view", "double_extension"]),
    }

    base_spec = next(spec for spec in specs if spec.key == AssetKey(["view", "base"]))
    assert base_spec.description == "This is the base view"

    extension_spec = next(spec for spec in specs if spec.key == AssetKey(["view", "extension"]))
    assert extension_spec.description == "This is an extension view"

    double_extension_spec = next(
        spec for spec in specs if spec.key == AssetKey(["view", "double_extension"])
    )
    # Latest extension should take precedence
    assert double_extension_spec.description == "This is an extension view"

    assert base_spec.deps and (base_spec.deps == extension_spec.deps)


def test_with_asset_key_replacements() -> None:
    class CustomDagsterLookerTranslator(DagsterLookerLkmlTranslator):
        def get_asset_spec(
            self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
        ) -> AssetSpec:
            default_spec = super().get_asset_spec(lookml_structure)
            return default_spec.replace_attributes(
                key=default_spec.key.with_prefix("prefix"),
            )

    my_looker_assets = build_looker_asset_specs(
        project_dir=test_retail_demo_path,
        dagster_looker_translator=CustomDagsterLookerTranslator(),
    )

    for spec in my_looker_assets:
        assert spec.deps
        assert spec.key.has_prefix(["prefix"])
        assert all(dep.asset_key.has_prefix(["prefix"]) for dep in spec.deps)


def test_with_asset_key_replacements_legacy() -> None:
    class CustomDagsterLookerTranslator(DagsterLookerLkmlTranslator):
        def get_asset_key(
            self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
        ) -> AssetKey:
            return super().get_asset_key(lookml_structure).with_prefix("prefix")

    my_looker_assets = build_looker_asset_specs(
        project_dir=test_retail_demo_path,
        dagster_looker_translator=CustomDagsterLookerTranslator(),
    )

    for spec in my_looker_assets:
        assert spec.deps
        assert spec.key.has_prefix(["prefix"])
        assert all(dep.asset_key.has_prefix(["prefix"]) for dep in spec.deps)


def test_with_deps_replacements() -> None:
    class CustomDagsterLookerTranslator(DagsterLookerLkmlTranslator):
        def get_asset_spec(
            self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
        ) -> AssetSpec:
            default_spec = super().get_asset_spec(lookml_structure)
            return default_spec.replace_attributes(deps=[])

    my_looker_assets = build_looker_asset_specs(
        project_dir=test_retail_demo_path,
        dagster_looker_translator=CustomDagsterLookerTranslator(),
    )

    for spec in my_looker_assets:
        assert not spec.deps


def test_with_deps_replacements_legacy() -> None:
    class CustomDagsterLookerTranslator(DagsterLookerLkmlTranslator):
        def get_deps(self, _) -> Sequence[AssetKey]:
            return []

    my_looker_assets = build_looker_asset_specs(
        project_dir=test_retail_demo_path,
        dagster_looker_translator=CustomDagsterLookerTranslator(),
    )

    for spec in my_looker_assets:
        assert not spec.deps


def test_with_description_replacements() -> None:
    expected_description = "customized description"

    class CustomDagsterLookerTranslator(DagsterLookerLkmlTranslator):
        def get_asset_spec(
            self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
        ) -> AssetSpec:
            default_spec = super().get_asset_spec(lookml_structure)
            return default_spec.replace_attributes(description=expected_description)

    my_looker_assets = build_looker_asset_specs(
        project_dir=test_retail_demo_path,
        dagster_looker_translator=CustomDagsterLookerTranslator(),
    )

    for spec in my_looker_assets:
        assert spec.description == expected_description


def test_with_description_replacements_legacy() -> None:
    expected_description = "customized description"

    class CustomDagsterLookerTranslator(DagsterLookerLkmlTranslator):
        def get_description(self, _) -> Optional[str]:
            return expected_description

    my_looker_assets = build_looker_asset_specs(
        project_dir=test_retail_demo_path,
        dagster_looker_translator=CustomDagsterLookerTranslator(),
    )

    for spec in my_looker_assets:
        assert spec.description == expected_description


def test_with_metadata_replacements() -> None:
    expected_metadata = {"customized": "metadata"}

    class CustomDagsterLookerTranslator(DagsterLookerLkmlTranslator):
        def get_asset_spec(
            self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
        ) -> AssetSpec:
            default_spec = super().get_asset_spec(lookml_structure)
            return default_spec.merge_attributes(metadata=expected_metadata)

    my_looker_assets = build_looker_asset_specs(
        project_dir=test_retail_demo_path,
        dagster_looker_translator=CustomDagsterLookerTranslator(),
    )

    for spec in my_looker_assets:
        assert "customized" in spec.metadata
        assert spec.metadata["customized"] == expected_metadata["customized"]


def test_with_metadata_replacements_legacy() -> None:
    expected_metadata = {"customized": "metadata"}

    class CustomDagsterLookerTranslator(DagsterLookerLkmlTranslator):
        def get_metadata(self, _) -> Optional[Mapping[str, Any]]:
            return expected_metadata

    my_looker_assets = build_looker_asset_specs(
        project_dir=test_retail_demo_path,
        dagster_looker_translator=CustomDagsterLookerTranslator(),
    )

    for spec in my_looker_assets:
        assert spec.metadata == expected_metadata


def test_with_group_replacements_legacy() -> None:
    expected_group = "customized_group"

    class CustomDagsterLookerTranslator(DagsterLookerLkmlTranslator):
        def get_group_name(self, _) -> Optional[str]:
            return expected_group

    my_looker_assets = build_looker_asset_specs(
        project_dir=test_retail_demo_path,
        dagster_looker_translator=CustomDagsterLookerTranslator(),
    )

    for spec in my_looker_assets:
        assert spec.group_name == expected_group


def test_with_owner_replacements_legacy() -> None:
    expected_owners = ["custom@custom.com"]

    class CustomDagsterLookerTranslator(DagsterLookerLkmlTranslator):
        def get_owners(self, _) -> Optional[Sequence[str]]:
            return expected_owners

    my_looker_assets = build_looker_asset_specs(
        project_dir=test_retail_demo_path,
        dagster_looker_translator=CustomDagsterLookerTranslator(),
    )

    for spec in my_looker_assets:
        assert spec.owners == expected_owners


def test_with_tag_replacements_legacy() -> None:
    expected_tags = {"customized": "tag"}

    class CustomDagsterLookerTranslator(DagsterLookerLkmlTranslator):
        def get_tags(self, _) -> Optional[Mapping[str, str]]:
            return expected_tags

    my_looker_assets = build_looker_asset_specs(
        project_dir=test_retail_demo_path,
        dagster_looker_translator=CustomDagsterLookerTranslator(),
    )

    for spec in my_looker_assets:
        assert spec.tags == expected_tags
