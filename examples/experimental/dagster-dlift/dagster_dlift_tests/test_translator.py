from dagster import AssetCheckSpec, AssetKey, AssetSpec
from dagster_dlift.translator import DagsterDbtCloudTranslator

from dagster_dlift_tests.conftest import create_jaffle_shop_project


def test_asset_spec_creation() -> None:
    data = create_jaffle_shop_project().compute_data()
    for model in data.models_by_unique_id:
        spec = DagsterDbtCloudTranslator(data).get_spec(data.models_by_unique_id[model])
        assert isinstance(spec, AssetSpec)
        assert spec.key == AssetKey(model)
    for source in data.sources_by_unique_id:
        spec = DagsterDbtCloudTranslator(data).get_spec(data.sources_by_unique_id[source])
        assert isinstance(spec, AssetSpec)
        assert spec.key == AssetKey(source)
    for test in data.tests_by_unique_id:
        spec = DagsterDbtCloudTranslator(data).get_spec(data.tests_by_unique_id[test])
        assert isinstance(spec, AssetCheckSpec)
        assert spec.name == test
        assert spec.asset_key == AssetKey(test)
