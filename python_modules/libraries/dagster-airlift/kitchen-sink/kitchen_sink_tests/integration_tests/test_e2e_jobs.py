import datetime

import pytest
from dagster import _check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.metadata.metadata_value import TimestampMetadataValue
from dagster._core.definitions.run_config import RunConfig
from dagster._core.event_api import EventRecordsFilter
from dagster._core.events import DagsterEventType
from dagster._core.instance import DagsterInstance
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.dagster_run import DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import EXTERNAL_JOB_SOURCE_TAG_KEY, EXTERNALLY_MANAGED_ASSETS_TAG
from dagster_airlift.constants import (
    DAG_ID_TAG_KEY,
    DAG_RUN_ID_TAG_KEY,
    OBSERVATION_RUN_TAG_KEY,
    TASK_ID_TAG_KEY,
)
from dagster_airlift.core.monitoring_job.builder import MonitoringConfig, monitoring_job_op_name
from dagster_airlift.core.utils import monitoring_job_name
from dagster_airlift.test.test_utils import asset_spec
from dagster_test.utils.definitions_execute_in_process import definitions_execute_job_in_process
from kitchen_sink.airflow_instance import local_airflow_instance

from kitchen_sink_tests.integration_tests.conftest import (
    makefile_dir,
    poll_for_airflow_run_existence_and_completion,
)


def test_job_based_defs(
    airflow_instance: None,
) -> None:
    """Test that job based defs load properly."""
    from kitchen_sink.dagster_defs.job_based_defs import defs

    assert len(defs.jobs) == 21  # type: ignore
    assert len(defs.assets) == 4  # type: ignore
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
        result = definitions_execute_job_in_process(
            defs=defs,
            job_name=monitoring_job_name(af_instance.name),
            instance=instance,
            run_config=RunConfig(
                ops={
                    monitoring_job_op_name(af_instance): MonitoringConfig(
                        range_start=(
                            datetime.datetime.now() - datetime.timedelta(seconds=30)
                        ).isoformat(),
                        range_end=datetime.datetime.now().isoformat(),
                    )
                }
            ),
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


@pytest.fixture(name="dagster_dev_cmd")
def dagster_dev_cmd_fixture() -> list[str]:
    return ["make", "run_job_based_defs", "-C", str(makefile_dir())]


def test_job_based_defs_with_proxied_assets(
    airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
) -> None:
    from kitchen_sink.dagster_defs.job_based_defs import defs

    af_instance = local_airflow_instance()
    with DagsterInstance.get() as instance:
        # Execute print_dag. We'd expect corresponding runs to be kicked off of print_asset and another_print_asset.
        print_dag_run_id = af_instance.trigger_dag("deferred_events_dag")
        poll_for_airflow_run_existence_and_completion(
            af_instance=af_instance,
            af_run_id=print_dag_run_id,
            dag_id="deferred_events_dag",
            duration=30,
        )

        # First, there should be "asset-less" runs for print_asset and another_print_asset
        print_task_run = next(
            iter(
                instance.get_run_records(
                    filters=RunsFilter(
                        tags={
                            TASK_ID_TAG_KEY: "print_task",
                            DAG_ID_TAG_KEY: "deferred_events_dag",
                            DAG_RUN_ID_TAG_KEY: print_dag_run_id,
                            EXTERNALLY_MANAGED_ASSETS_TAG: "true",
                        }
                    )
                )
            )
        )
        assert print_task_run.dagster_run.status == DagsterRunStatus.SUCCESS

        # Attempt to retrieve materialization events and planned events scoped to the run. They should be empty.
        conn = instance.event_log_storage.get_records_for_run(
            run_id=print_task_run.dagster_run.run_id,
            of_type={
                DagsterEventType.ASSET_MATERIALIZATION,
                DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
            },
        )
        assert len(conn.records) == 0

        # Same for downstream_print_task
        downstream_print_task_run = next(
            iter(
                instance.get_run_records(
                    filters=RunsFilter(
                        tags={
                            TASK_ID_TAG_KEY: "downstream_print_task",
                            DAG_ID_TAG_KEY: "deferred_events_dag",
                            DAG_RUN_ID_TAG_KEY: print_dag_run_id,
                            EXTERNALLY_MANAGED_ASSETS_TAG: "true",
                        }
                    )
                )
            )
        )
        assert downstream_print_task_run.dagster_run.status == DagsterRunStatus.SUCCESS

        # Attempt to retrieve materialization events and planned events scoped to the run. They should be empty.
        conn = instance.event_log_storage.get_records_for_run(
            run_id=downstream_print_task_run.dagster_run.run_id,
            of_type={
                DagsterEventType.ASSET_MATERIALIZATION,
                DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
            },
        )
        assert len(conn.records) == 0

        # Execute the monitoring job in process.
        result = definitions_execute_job_in_process(
            defs=defs,
            job_name=monitoring_job_name(af_instance.name),
            instance=instance,
            run_config=RunConfig(
                ops={
                    monitoring_job_op_name(af_instance): MonitoringConfig(
                        range_start=(
                            datetime.datetime.now() - datetime.timedelta(seconds=300)
                        ).isoformat(),
                        range_end=datetime.datetime.now().isoformat(),
                    )
                }
            ),
        )
        assert result.success

        # Check that the print_asset was materialized, and that the metadata from the run was included.
        observed_run = next(
            iter(
                instance.get_run_records(
                    filters=RunsFilter(
                        tags={
                            DAG_ID_TAG_KEY: "deferred_events_dag",
                            DAG_RUN_ID_TAG_KEY: print_dag_run_id,
                            OBSERVATION_RUN_TAG_KEY: "true",
                        }
                    )
                )
            )
        )
        assert observed_run.dagster_run.status == DagsterRunStatus.SUCCESS
        conn = instance.event_log_storage.get_records_for_run(
            run_id=observed_run.dagster_run.run_id,
            of_type={DagsterEventType.ASSET_MATERIALIZATION},
        )
        assert len(conn.records) == 2
        materializations = [
            check.not_none(r.event_log_entry.asset_materialization) for r in conn.records
        ]
        assert {m.asset_key for m in materializations} == {
            AssetKey("print_asset"),
            AssetKey("another_print_asset"),
        }
        print_mat = next(m for m in materializations if m.asset_key == AssetKey("print_asset"))
        assert print_mat.metadata["foo"].value == "bar"
        another_print_mat = next(
            m for m in materializations if m.asset_key == AssetKey("another_print_asset")
        )
        assert another_print_mat.metadata["foo"].value == "baz"
