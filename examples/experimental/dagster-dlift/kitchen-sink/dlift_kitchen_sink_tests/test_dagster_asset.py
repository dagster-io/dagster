from dagster import materialize_to_memory
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.instance import DagsterInstance
from dagster._core.test_utils import instance_for_test
from dlift_kitchen_sink.defs import dbt_models


def assert_materialization(instance: DagsterInstance, asset_key: AssetKey) -> None:
    records_result = instance.fetch_materializations(asset_key, limit=1)
    assert len(records_result.records) == 1


def assert_check_result(instance: DagsterInstance, check_key: AssetCheckKey) -> None:
    records_result = instance.get_latest_asset_check_evaluation_record(check_key)
    assert records_result
    assert records_result.evaluation
    assert records_result.evaluation.passed


def test_dbt_models(ensure_cleanup: None) -> None:
    """Test that dbt models can be successfully materialized, and that a run and job exist in the dbt cloud project."""
    with instance_for_test() as instance:
        result = materialize_to_memory(assets=[dbt_models], instance=instance)
        assert result.success
        for spec in dbt_models.specs:
            assert_materialization(instance, spec.key)
        for check_spec in dbt_models.check_specs:
            assert_check_result(instance, check_spec.key)
