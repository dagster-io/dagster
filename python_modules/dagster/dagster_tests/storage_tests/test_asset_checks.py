import pytest
from dagster import DagsterInstance, asset
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.decorators.asset_check_decorator import asset_check
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.test_utils import instance_for_test


@pytest.fixture
def instance():
    with instance_for_test() as instance:
        yield instance


@asset
def the_asset():
    return 1


@asset_check(asset=the_asset)
def the_asset_check():
    return AssetCheckResult(passed=True)


defs = Definitions(assets=[the_asset], asset_checks=[the_asset_check])


def test_get_asset_check_summary_records(instance: DagsterInstance):
    records = instance.event_log_storage.get_asset_check_summary_records(
        asset_check_keys=list(the_asset_check.check_keys)
    )
    assert len(records) == 1
    check_key = the_asset_check.check_key
    summary_record = records[check_key]
    assert summary_record.asset_check_key == next(iter(the_asset_check.check_keys))
    assert summary_record.last_check_execution_record is None
    assert summary_record.last_run_id is None
    implicit_job = defs.get_all_job_defs()[0]
    result = implicit_job.execute_in_process(instance=instance)
    assert result.success
    records = instance.event_log_storage.get_asset_check_summary_records(
        asset_check_keys=list(the_asset_check.check_keys)
    )
    assert len(records) == 1
    assert records[check_key].last_check_execution_record.event.asset_check_evaluation.passed  # type: ignore
    assert records[check_key].last_run_id == result.run_id
