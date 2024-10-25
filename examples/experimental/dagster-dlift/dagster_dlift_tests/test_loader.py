from dagster_dlift.loader import DbtCloudProjectEnvironmentDefsLoader
from dagster_dlift.translator import DbtCloudContentType

from dagster_dlift_tests.conftest import create_jaffle_shop_project


def test_multi_load() -> None:
    """Test creation of data from a test environment."""
    project = create_jaffle_shop_project()
    loader = DbtCloudProjectEnvironmentDefsLoader(project_environment=project)
    data = loader.get_or_fetch_state()
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
    assert data == loader.get_or_fetch_state()
