from dagster import repository
from dagster._core.definitions.assets_job import build_assets_job
from dagster._core.definitions.data_version import (
    extract_data_version_from_entry,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.instance_for_test import instance_for_test
from dagster._core.test_utils import create_test_asset_job
from docs_snippets.concepts.assets.observable_source_assets import (
    foo_source_asset,
    observation_job,
    observation_schedule,
)


def test_observable_source_asset():
    job_def = create_test_asset_job([foo_source_asset])
    result = job_def.execute_in_process()
    assert result.success


def test_observable_source_asset_job():
    with instance_for_test() as instance:
        Definitions(
            assets=[foo_source_asset],
            jobs=[observation_job],
        ).get_job_def("observation_job").execute_in_process(instance=instance)

        record = instance.get_latest_data_version_record(foo_source_asset.key)
        assert record
        assert extract_data_version_from_entry(record.event_log_entry)


def test_observable_source_asset_schedule():
    assert observation_schedule.name == "observation_schedule"
    assert observation_schedule.cron_schedule == "@daily"
