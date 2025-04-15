from dagster import _check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.metadata.metadata_value import TimestampMetadataValue
from dagster._core.event_api import EventRecordsFilter
from dagster._core.events import DagsterEventType
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.storage.tags import EXTERNAL_JOB_SOURCE_TAG_KEY
from dagster_airlift.constants import DAG_ID_TAG_KEY, DAG_RUN_ID_TAG_KEY
from dagster_airlift.core.utils import monitoring_job_name
from dagster_airlift.test.test_utils import asset_spec
from kitchen_sink.airflow_instance import local_airflow_instance

from kitchen_sink_tests.integration_tests.conftest import (
    poll_for_airflow_run_existence_and_completion,
)


def test_job_based_defs(
    airflow_instance: None,
) -> None:
    """Test that job based defs load properly."""
    from kitchen_sink.dagster_defs.job_based_defs import defs

    assert len(defs.jobs) == 20  # type: ignore
    assert len(defs.assets) == 1  # type: ignore
    for key in ["print_asset", "another_print_asset", "example1", "example2"]:
        assert asset_spec(key, defs)

    # First, execute dataset producer dag
    af_instance = local_airflow_instance()
    af_run_id = af_instance.trigger_dag("dataset_producer")
    poll_for_airflow_run_existence_and_completion(
        af_instance=af_instance, af_run_id=af_run_id, dag_id="dataset_producer", duration=30
    )

    # Then, execute monitoring job
    with instance_for_test() as instance:
        result = defs.execute_job_in_process(
            monitoring_job_name(af_instance.name), instance=instance
        )
        assert result.success
        # There should be a run for the dataset producer dag and a run for the monitoring job
        runs = instance.get_runs()
        assert len(runs) == 2

        producer_run = next(run for run in runs if run.job_name == "dataset_producer")
        assert producer_run.status == DagsterRunStatus.SUCCESS
        assert producer_run.tags[DAG_RUN_ID_TAG_KEY] == af_run_id
        assert producer_run.tags[DAG_ID_TAG_KEY] == "dataset_producer"
        assert producer_run.tags[EXTERNAL_JOB_SOURCE_TAG_KEY] == "airflow"

        # Check that there are asset planned events for the two assets
        planned_records = instance.get_event_records(
            event_records_filter=EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED
            ),
        )
        assert len(planned_records) == 2
        assert {planned_records.asset_key for planned_records in planned_records} == {
            AssetKey("example1"),
            AssetKey("example2"),
        }
        assert {planned_records.run_id for planned_records in planned_records} == {
            producer_run.run_id
        }

        # Check that there are asset materialized events for the two assets
        materialized_records = instance.get_event_records(
            event_records_filter=EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION
            ),
        )
        assert len(materialized_records) == 2
        assert {
            materialized_records.asset_key for materialized_records in materialized_records
        } == {
            AssetKey("example1"),
            AssetKey("example2"),
        }
        assert {materialized_records.run_id for materialized_records in materialized_records} == {
            producer_run.run_id
        }
        for key in ["example1", "example2"]:
            key_record = next(
                materialized_records
                for materialized_records in materialized_records
                if materialized_records.asset_key == AssetKey(key)
            )
            asset_metadata = check.not_none(key_record.asset_materialization).metadata

            assert asset_metadata["my_timestamp"] == TimestampMetadataValue(value=111.0)
            assert asset_metadata["my_other_timestamp"] == TimestampMetadataValue(value=113.0)
            # It gets overridden by the second print
            assert asset_metadata["foo"].value == "baz"
