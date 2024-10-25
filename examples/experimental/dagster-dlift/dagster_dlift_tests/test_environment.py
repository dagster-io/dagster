from dagster import AssetCheckKey, AssetKey
from dagster_dlift.translator import DbtCloudContentType

from dagster_dlift_tests.conftest import create_jaffle_shop_project


def test_environment_data_creation() -> None:
    """Test creation of data from a test environment."""
    project = create_jaffle_shop_project()
    data = project.compute_data()
    assert set(data.models_by_unique_id.keys()) == {
        "model.jaffle_shop.customers",
        "model.jaffle_shop.stg_customers",
        "model.jaffle_shop.stg_orders",
    }
    assert set(data.sources_by_unique_id.keys()) == {
        "source.jaffle_shop.jaffle_shop.customers",
        "source.jaffle_shop.jaffle_shop.orders",
    }
    assert set(data.tests_by_unique_id.keys()) == {
        "test.jaffle_shop.customers",
        "test.jaffle_shop.orders",
    }
    assert all(
        data.models_by_unique_id[model].content_type == DbtCloudContentType.MODEL
        for model in data.models_by_unique_id
    )
    assert all(
        data.sources_by_unique_id[source].content_type == DbtCloudContentType.SOURCE
        for source in data.sources_by_unique_id
    )
    assert all(
        data.tests_by_unique_id[test].content_type == DbtCloudContentType.TEST
        for test in data.tests_by_unique_id
    )


def test_spec_retrieval() -> None:
    dbt_cloud_project = create_jaffle_shop_project()

    asset_specs = dbt_cloud_project.get_asset_specs()
    assert {spec.key for spec in asset_specs} == {
        AssetKey("model_jaffle_shop_customers"),
        AssetKey("model_jaffle_shop_stg_customers"),
        AssetKey("model_jaffle_shop_stg_orders"),
        AssetKey("source_jaffle_shop_jaffle_shop_customers"),
        AssetKey("source_jaffle_shop_jaffle_shop_orders"),
    }
    check_specs = dbt_cloud_project.get_check_specs()
    assert {spec.key for spec in check_specs} == {
        AssetCheckKey(
            name="test_jaffle_shop_customers", asset_key=AssetKey("model_jaffle_shop_stg_customers")
        ),
        AssetCheckKey(
            name="test_jaffle_shop_orders", asset_key=AssetKey("model_jaffle_shop_stg_orders")
        ),
    }
