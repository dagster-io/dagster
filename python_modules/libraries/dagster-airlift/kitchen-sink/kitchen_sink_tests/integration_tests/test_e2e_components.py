from datetime import datetime, timedelta

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.metadata.metadata_value import TimestampMetadataValue
from dagster._core.definitions.run_config import RunConfig
from dagster._core.event_api import EventRecordsFilter
from dagster._core.events import DagsterEventType
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.storage.tags import EXTERNAL_JOB_SOURCE_TAG_KEY
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster_airlift.constants import DAG_ID_TAG_KEY, DAG_RUN_ID_TAG_KEY
from dagster_airlift.core.monitoring_job.builder import MonitoringConfig, monitoring_job_op_name
from dagster_airlift.core.utils import monitoring_job_name
from dagster_airlift.test.test_utils import asset_spec
from dagster_test.utils.definitions_execute_in_process import definitions_execute_job_in_process
from kitchen_sink.airflow_instance import local_airflow_instance

from kitchen_sink_tests.integration_tests.conftest import (
    poll_for_airflow_run_existence_and_completion,
)


def test_component_based_defs(
    airflow_instance: None,
) -> None:
    """Test that component based defs load properly."""
    with instance_for_test() as instance:
        with scoped_definitions_load_context():
            from kitchen_sink.dagster_defs.component_defs import defs

        assert len(defs.jobs) == 21  # type: ignore
        assert len(defs.assets) == 2  # type: ignore
        assert len(defs.sensors) == 1  # type: ignore
        for key in ["example1", "example2"]:
            assert asset_spec(key, defs)

        # First, execute dataset producer dag
        af_instance = local_airflow_instance("kitchen_sink_instance")
        af_run_id = af_instance.trigger_dag("dataset_producer")
        poll_for_airflow_run_existence_and_completion(
            af_instance=af_instance, af_run_id=af_run_id, dag_id="dataset_producer", duration=30
        )

        # Then, execute monitoring job
        result = definitions_execute_job_in_process(
            defs=defs,
            job_name=monitoring_job_name(af_instance.name),
            instance=instance,
            run_config=RunConfig(
                ops={
                    monitoring_job_op_name(af_instance): MonitoringConfig(
                        range_start=(datetime.now() - timedelta(seconds=30)).isoformat(),
                        range_end=datetime.now().isoformat(),
                    )
                }
            ),
        )
        assert result.success
        # There should be a run for the dataset producer dag
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
            metadata = key_record.asset_materialization.metadata  # type: ignore
            assert metadata["my_timestamp"] == TimestampMetadataValue(value=111.0)
            assert metadata["my_other_timestamp"] == TimestampMetadataValue(value=113.0)
            assert metadata["foo"].value == "baz"
