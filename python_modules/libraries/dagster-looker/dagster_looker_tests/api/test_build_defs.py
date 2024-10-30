from typing import Iterator

import pytest
import responses
from dagster import AssetKey, AssetSpec, Definitions, materialize
from dagster_looker import (
    LookerFilter,
    LookerResource,
    load_looker_asset_specs_from_instance,
    load_looker_view_specs_from_project,
)
from dagster_looker.api.assets import build_looker_pdt_assets_definitions
from dagster_looker.api.dagster_looker_api_translator import (
    DagsterLookerApiTranslator,
    LookerStructureData,
    RequestStartPdtBuild,
)

from dagster_looker_tests.api.mock_looker_data import (
    mock_check_pdt_build,
    mock_folders,
    mock_looker_dashboard,
    mock_looker_dashboard_bases,
    mock_lookml_explore,
    mock_lookml_models,
    mock_lookml_other_explore,
    mock_other_looker_dashboard,
    mock_start_pdt_build,
)

TEST_BASE_URL = "https://your.cloud.looker.com"


@pytest.fixture(name="looker_resource")
def looker_resource_fixture() -> LookerResource:
    return LookerResource(
        base_url=TEST_BASE_URL, client_id="client_id", client_secret="client_secret"
    )


@pytest.fixture(name="looker_instance_data_mocks")
def looker_instance_data_mocks_fixture(
    looker_resource: LookerResource,
) -> Iterator[responses.RequestsMock]:
    sdk = looker_resource.get_sdk()

    with responses.RequestsMock() as response:
        # Mock the login request
        responses.add(method=responses.POST, url=f"{TEST_BASE_URL}/api/4.0/login", json={})

        # Mock the request for all lookml models
        responses.add(
            method=responses.GET,
            url=f"{TEST_BASE_URL}/api/4.0/lookml_models",
            body=sdk.serialize(api_model=mock_lookml_models),  # type: ignore
        )

        # Mock the request for a single lookml explore
        responses.add(
            method=responses.GET,
            url=f"{TEST_BASE_URL}/api/4.0/lookml_models/my_model/explores/my_explore",
            body=sdk.serialize(api_model=mock_lookml_explore),  # type: ignore
        )
        responses.add(
            method=responses.GET,
            url=f"{TEST_BASE_URL}/api/4.0/lookml_models/my_model/explores/my_other_explore",
            body=sdk.serialize(api_model=mock_lookml_other_explore),  # type: ignore
        )

        # Mock the request for all looker dashboards
        responses.add(
            method=responses.GET,
            url=f"{TEST_BASE_URL}/api/4.0/folders",
            body=sdk.serialize(api_model=mock_folders),  # type: ignore
        )

        # Mock the request for all looker dashboards
        responses.add(
            method=responses.GET,
            url=f"{TEST_BASE_URL}/api/4.0/dashboards",
            body=sdk.serialize(api_model=mock_looker_dashboard_bases),  # type: ignore
        )

        # Mock the request for a single looker dashboard
        responses.add(
            method=responses.GET,
            url=f"{TEST_BASE_URL}/api/4.0/dashboards/1",
            body=sdk.serialize(api_model=mock_looker_dashboard),  # type: ignore
        )

        responses.add(
            method=responses.GET,
            url=f"{TEST_BASE_URL}/api/4.0/dashboards/2",
            body=sdk.serialize(api_model=mock_other_looker_dashboard),  # type: ignore
        )

        yield response


@responses.activate
def test_load_asset_specs_filter(
    looker_resource: LookerResource, looker_instance_data_mocks: responses.RequestsMock
) -> None:
    asset_specs_by_key = {
        spec.key: spec
        for spec in load_looker_asset_specs_from_instance(
            looker_resource,
            looker_filter=LookerFilter(
                dashboard_folders=[["my_folder", "my_subfolder"]],
                only_fetch_explores_used_in_dashboards=True,
            ),
        )
    }

    assert len(asset_specs_by_key) == 2
    assert AssetKey(["my_dashboard_2"]) not in asset_specs_by_key
    assert AssetKey(["my_model::my_other_explore"]) not in asset_specs_by_key


@responses.activate
def test_load_asset_specs(
    looker_resource: LookerResource, looker_instance_data_mocks: responses.RequestsMock
) -> None:
    asset_specs_by_key = {
        spec.key: spec for spec in load_looker_asset_specs_from_instance(looker_resource)
    }

    assert len(asset_specs_by_key) == 4

    expected_lookml_view_asset_dep_key = AssetKey(["view", "my_view"])
    expected_lookml_explore_asset_key = AssetKey(["my_model::my_explore"])
    expected_looker_dashboard_asset_key = AssetKey(["my_dashboard_1"])

    lookml_explore_asset = asset_specs_by_key[expected_lookml_explore_asset_key]
    assert [dep.asset_key for dep in lookml_explore_asset.deps] == [
        expected_lookml_view_asset_dep_key
    ]
    assert lookml_explore_asset.tags == {"dagster/kind/looker": "", "dagster/kind/explore": ""}

    looker_dashboard_asset = asset_specs_by_key[expected_looker_dashboard_asset_key]
    assert [dep.asset_key for dep in looker_dashboard_asset.deps] == [
        expected_lookml_explore_asset_key
    ]
    assert looker_dashboard_asset.tags == {"dagster/kind/looker": "", "dagster/kind/dashboard": ""}


@responses.activate
def test_build_defs_with_pdts(
    looker_resource: LookerResource, looker_instance_data_mocks: responses.RequestsMock
) -> None:
    resource_key = "looker"

    pdts = build_looker_pdt_assets_definitions(
        resource_key=resource_key,
        request_start_pdt_builds=[RequestStartPdtBuild(model_name="my_model", view_name="my_view")],
    )

    defs = Definitions(
        assets=[*pdts, *load_looker_asset_specs_from_instance(looker_resource)],
        resources={resource_key: looker_resource},
    )

    assert len(defs.get_all_asset_specs()) == 5

    sdk = looker_resource.get_sdk()

    responses.add(
        method=responses.GET,
        url=f"{TEST_BASE_URL}/api/4.0/derived_table/my_model/my_view/start",
        body=sdk.serialize(api_model=mock_start_pdt_build),  # type: ignore
    )

    responses.add(
        method=responses.GET,
        url=f"{TEST_BASE_URL}/api/4.0/derived_table/{mock_start_pdt_build.materialization_id}/status",
        body=sdk.serialize(api_model=mock_check_pdt_build),  # type: ignore
    )

    pdt = defs.get_repository_def().assets_defs_by_key[AssetKey(["view", "my_view"])]
    result = materialize([pdt])

    assert result.success


@responses.activate
def test_custom_asset_specs(
    looker_resource: LookerResource, looker_instance_data_mocks: responses.RequestsMock
) -> None:
    expected_metadata = {"custom": "metadata"}

    class CustomDagsterLookerApiTranslator(DagsterLookerApiTranslator):
        def get_asset_key(self, looker_structure: LookerStructureData) -> AssetKey:
            return super().get_asset_key(looker_structure).with_prefix("my_prefix")

        def get_asset_spec(self, looker_structure: LookerStructureData) -> AssetSpec:
            return super().get_asset_spec(looker_structure)._replace(metadata=expected_metadata)

    all_assets = (
        asset
        for asset in Definitions(
            assets=[
                *load_looker_asset_specs_from_instance(
                    looker_resource, CustomDagsterLookerApiTranslator
                )
            ],
        )
        .get_asset_graph()
        .assets_defs
        if not asset.is_auto_created_stub
    )

    for asset in all_assets:
        for metadata in asset.metadata_by_key.values():
            assert metadata == expected_metadata
        assert all(key.path[0] == "my_prefix" for key in asset.keys)


from dagster_looker_tests.looker_projects import test_retail_demo_path


def test_load_view_deps() -> None:
    my_looker_assets = load_looker_view_specs_from_project(project_dir=test_retail_demo_path)
    asset_deps = {}
    for spec in my_looker_assets:
        asset_deps[spec.key] = {dep.asset_key for dep in spec.deps}

    assert asset_deps == {
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
