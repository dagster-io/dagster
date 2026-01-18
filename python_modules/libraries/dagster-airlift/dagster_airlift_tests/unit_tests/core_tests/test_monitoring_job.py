import json
from datetime import datetime, timedelta, timezone

import dagster._check as check
import pytest
from dagster import AssetKey, DagsterInstance
from dagster._core.definitions import materialize
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.metadata.metadata_value import TextMetadataValue
from dagster._core.definitions.run_config import RunConfig
from dagster._core.definitions.run_request import RunRequest, SkipReason
from dagster._core.definitions.sensor_definition import build_sensor_context
from dagster._core.events import DagsterEvent
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import (
    EXTERNALLY_MANAGED_ASSETS_TAG,
    REPOSITORY_LABEL_TAG,
    ROOT_RUN_ID_TAG,
)
from dagster._core.test_utils import freeze_time
from dagster._core.utils import make_new_run_id
from dagster_airlift.constants import (
    DAG_ID_TAG_KEY,
    DAG_RUN_ID_TAG_KEY,
    OBSERVATION_RUN_TAG_KEY,
    TASK_ID_TAG_KEY,
)
from dagster_airlift.core.job_builder import job_name
from dagster_airlift.core.load_defs import (
    build_defs_from_airflow_instance,
    build_job_based_airflow_defs,
)
from dagster_airlift.core.monitoring_job.builder import (
    MonitoringConfig,
    build_airflow_monitoring_defs,
    monitoring_job_op_name,
)
from dagster_airlift.core.serialization.defs_construction import make_default_dag_asset_key
from dagster_airlift.core.utils import monitoring_job_name
from dagster_airlift.test import make_dag_run, make_task_instance
from dagster_test.utils.definitions_execute_in_process import definitions_execute_job_in_process

from dagster_airlift_tests.unit_tests.conftest import create_defs_and_instance


def make_dag_key(dag_id: str) -> AssetKey:
    return AssetKey(["test_instance", "dag", dag_id])


def make_dag_key_str(dag_id: str) -> str:
    return make_dag_key(dag_id).to_user_string()


def test_monitoring_job_execution(init_load_context: None, instance: DagsterInstance) -> None:
    """Test that monitoring job correctly represents state in Dagster."""
    freeze_datetime = datetime(2021, 1, 1, tzinfo=timezone.utc)

    raw_metadata = {
        "foo": "bar",
        "my_timestamp": {"raw_value": 111, "type": "timestamp"},
    }
    with freeze_time(freeze_datetime):
        defs, af_instance = create_defs_and_instance(
            assets_per_task={
                "dag": {"task": [("a", [])]},
                "dag2": {"task": [("b", [])]},
            },
            create_runs=False,
            create_assets_defs=False,
            seeded_runs=[
                # Have a newly started run.
                make_dag_run(
                    dag_id="dag",
                    run_id="run-dag",
                    start_date=freeze_datetime - timedelta(seconds=30),
                    end_date=None,
                    state="running",
                ),
                # Have a newly finished run in success state. We also need to create a corresponding run on the instance
                # for this.
                make_dag_run(
                    dag_id="dag",
                    run_id="success-run",
                    start_date=freeze_datetime - timedelta(seconds=30),
                    end_date=freeze_datetime,
                    state="success",
                ),
                # Have a newly finished run in failed state. We also need to create a corresponding run on the instance
                # for this.
                make_dag_run(
                    dag_id="dag",
                    run_id="failure-run",
                    start_date=freeze_datetime - timedelta(seconds=30),
                    end_date=freeze_datetime,
                    state="failed",
                ),
                # Newly finished run that started after the last iteration, and therefore has no corresponding run on the instance.
                make_dag_run(
                    dag_id="dag2",
                    run_id="late-run",
                    start_date=freeze_datetime - timedelta(seconds=15),
                    end_date=freeze_datetime - timedelta(seconds=10),
                    state="success",
                ),
            ],
            seeded_task_instances=[
                # Have a newly completed task instance for the newly started run.
                make_task_instance(
                    dag_id="dag",
                    task_id="task",
                    run_id="run-dag",
                    start_date=freeze_datetime - timedelta(seconds=30),
                    end_date=freeze_datetime,
                ),
                # Have a newly completed task instance for the late run.
                make_task_instance(
                    dag_id="dag2",
                    task_id="task",
                    run_id="late-run",
                    start_date=freeze_datetime - timedelta(seconds=15),
                    end_date=freeze_datetime - timedelta(seconds=10),
                ),
            ],
            seeded_logs={
                "run-dag": {"task": f"DAGSTER_START{json.dumps(raw_metadata)}DAGSTER_END"}
            },
        )
        defs = build_job_based_airflow_defs(
            airflow_instance=af_instance,
            mapped_defs=defs,
        )
        success_dagster_run_id = make_new_run_id()
        instance.run_storage.add_historical_run(
            dagster_run=DagsterRun(
                job_name=job_name("dag"),
                run_id=success_dagster_run_id,
                tags={
                    DAG_RUN_ID_TAG_KEY: "success-run",
                    DAG_ID_TAG_KEY: "dag",
                    OBSERVATION_RUN_TAG_KEY: "true",
                },
                status=DagsterRunStatus.STARTED,
            ),
            run_creation_time=freeze_datetime - timedelta(seconds=30),
        )
        failure_dagster_run_id = make_new_run_id()
        instance.run_storage.add_historical_run(
            dagster_run=DagsterRun(
                job_name=job_name("dag"),
                run_id=failure_dagster_run_id,
                tags={
                    DAG_RUN_ID_TAG_KEY: "failure-run",
                    DAG_ID_TAG_KEY: "dag",
                    OBSERVATION_RUN_TAG_KEY: "true",
                },
            ),
            run_creation_time=freeze_datetime - timedelta(seconds=30),
        )
        result = definitions_execute_job_in_process(
            defs=defs,
            job_name=monitoring_job_name(af_instance.name),
            instance=instance,
            tags={REPOSITORY_LABEL_TAG: "placeholder"},
            run_config=RunConfig(
                ops={
                    monitoring_job_op_name(af_instance): MonitoringConfig(
                        range_start=(freeze_datetime - timedelta(seconds=30)).isoformat(),
                        range_end=freeze_datetime.isoformat(),
                    )
                }
            ),
        )
        assert result.success

        # Expect that the success and failure runs are marked as finished.
        success_record = check.not_none(instance.get_run_record_by_id(success_dagster_run_id))
        assert success_record.dagster_run.status == DagsterRunStatus.SUCCESS
        assert success_record.end_time == (freeze_datetime).timestamp()

        failure_record = check.not_none(instance.get_run_record_by_id(failure_dagster_run_id))
        assert failure_record.dagster_run.status == DagsterRunStatus.FAILURE
        assert failure_record.end_time == (freeze_datetime).timestamp()

        # Expect that we created a new run for the newly running run.
        newly_started_run_record = next(
            iter(instance.get_run_records(filters=RunsFilter(tags={DAG_RUN_ID_TAG_KEY: "run-dag"})))
        )
        assert newly_started_run_record.dagster_run.status == DagsterRunStatus.STARTED
        assert (
            newly_started_run_record.start_time
            == (freeze_datetime - timedelta(seconds=30)).timestamp()
        )

        late_run = next(
            iter(instance.get_runs(filters=RunsFilter(tags={DAG_RUN_ID_TAG_KEY: "late-run"})))
        )
        assert late_run.status == DagsterRunStatus.SUCCESS
        run_record = check.not_none(instance.get_run_record_by_id(late_run.run_id))
        assert (
            run_record.create_timestamp.timestamp()
            == (freeze_datetime - timedelta(seconds=15)).timestamp()
        )
        assert run_record.start_time == (freeze_datetime - timedelta(seconds=15)).timestamp()
        assert run_record.end_time == (freeze_datetime - timedelta(seconds=10)).timestamp()

        # There should be planned materialization data for the task.
        planned_info = instance.get_latest_planned_materialization_info(AssetKey("a"))
        assert planned_info
        assert planned_info.run_id == newly_started_run_record.dagster_run.run_id
        # Expect that we emitted asset materialization events for the task.
        mapped_asset_mat = instance.get_latest_materialization_event(AssetKey("a"))
        assert mapped_asset_mat is not None
        assert mapped_asset_mat.run_id == newly_started_run_record.dagster_run.run_id


def get_invalid_json_log_content() -> str:
    raw_metadata = {
        "foo": "bar",
        "my_timestamp": {"raw_value": 111, "type": "timestamp"},
    }
    return f"DAGSTER_START{json.dumps(raw_metadata)}ijkDAGSTER_END"  # add ijk randomly at the endto make it invalid json


def get_invalid_type_log_content() -> str:
    raw_metadata = {
        "foo": "bar",
        "my_timestamp": {"raw_value": 111, "type": "not_a_type"},
    }
    return f"DAGSTER_START{json.dumps(raw_metadata)}DAGSTER_END"


@pytest.mark.parametrize(
    "log_content",
    [
        get_invalid_json_log_content(),
        get_invalid_type_log_content(),
    ],
)
def test_monitoring_job_log_extraction_errors(
    init_load_context: None, instance: DagsterInstance, log_content: str
) -> None:
    """Test that monitoring job correctly handles log extraction errors."""
    freeze_datetime = datetime(2021, 1, 1, tzinfo=timezone.utc)

    with freeze_time(freeze_datetime):
        defs, af_instance = create_defs_and_instance(
            assets_per_task={
                "dag": {"task": [("a", [])]},
            },
            create_runs=False,
            create_assets_defs=False,
            seeded_runs=[
                # Have a newly started run.
                make_dag_run(
                    dag_id="dag",
                    run_id="run-dag",
                    start_date=freeze_datetime - timedelta(seconds=30),
                    end_date=None,
                    state="running",
                ),
            ],
            seeded_task_instances=[
                # Have a newly completed task instance for the newly started run.
                make_task_instance(
                    dag_id="dag",
                    task_id="task",
                    run_id="run-dag",
                    start_date=freeze_datetime - timedelta(seconds=30),
                    end_date=freeze_datetime,
                ),
            ],
            seeded_logs={"run-dag": {"task": log_content}},
        )
        defs = build_job_based_airflow_defs(
            airflow_instance=af_instance,
            mapped_defs=defs,
        )
        # Despite the invalid log content, we should still be able to execute the job.
        result = definitions_execute_job_in_process(
            defs=defs,
            job_name=monitoring_job_name(af_instance.name),
            instance=instance,
            tags={REPOSITORY_LABEL_TAG: "placeholder"},
            run_config=RunConfig(
                ops={
                    monitoring_job_op_name(af_instance): MonitoringConfig(
                        range_start=(freeze_datetime - timedelta(seconds=30)).isoformat(),
                        range_end=freeze_datetime.isoformat(),
                    )
                }
            ),
        )
        assert result.success
        newly_started_run = next(
            iter(instance.get_runs(filters=RunsFilter(tags={DAG_RUN_ID_TAG_KEY: "run-dag"})))
        )

        # Expect that we emitted asset materialization events for the task.
        mapped_asset_mat = instance.get_latest_materialization_event(AssetKey("a"))
        assert mapped_asset_mat is not None
        assert mapped_asset_mat.run_id == newly_started_run.run_id
        # metadata should be empty
        assert check.not_none(mapped_asset_mat.asset_materialization).metadata == {}


def test_monitoring_job_dag_assets(init_load_context: None, instance: DagsterInstance) -> None:
    """Test that monitoring job can correctly handle state when dag assets are used."""
    freeze_datetime = datetime(2021, 1, 1, tzinfo=timezone.utc)

    with freeze_time(freeze_datetime):
        defs, af_instance = create_defs_and_instance(
            assets_per_task={
                "dag": {"task": [("a", [])]},
            },
            create_runs=False,
            create_assets_defs=False,
            seeded_runs=[
                # Have a newly started run.
                make_dag_run(
                    dag_id="dag",
                    run_id="run-dag",
                    start_date=freeze_datetime - timedelta(seconds=30),
                    end_date=None,
                    state="running",
                ),
                # Have a newly finished run in success state. Since there's no jobs associated,
                # we don't need to create a corresponding run on the instance.
                make_dag_run(
                    dag_id="dag",
                    run_id="success-run",
                    start_date=freeze_datetime - timedelta(seconds=30),
                    end_date=freeze_datetime,
                    state="success",
                ),
                # Have a newly finished run in failed state. Since there's no jobs associated,
                # we don't need to create a corresponding run on the instance.
                make_dag_run(
                    dag_id="dag",
                    run_id="failure-run",
                    start_date=freeze_datetime - timedelta(seconds=30),
                    end_date=freeze_datetime,
                    state="failed",
                ),
            ],
            seeded_task_instances=[
                # Have a newly completed task instance for the newly started run.
                make_task_instance(
                    dag_id="dag",
                    task_id="task",
                    run_id="run-dag",
                    start_date=freeze_datetime - timedelta(seconds=30),
                    end_date=freeze_datetime,
                ),
            ],
        )
        enriched_defs = build_defs_from_airflow_instance(
            airflow_instance=af_instance,
            defs=defs,
        )
        full_defs = Definitions.merge(
            enriched_defs, build_airflow_monitoring_defs(airflow_instance=af_instance)
        )
        result = definitions_execute_job_in_process(
            defs=full_defs,
            job_name=monitoring_job_name(af_instance.name),
            instance=instance,
            tags={REPOSITORY_LABEL_TAG: "placeholder"},
            run_config=RunConfig(
                ops={
                    monitoring_job_op_name(af_instance): MonitoringConfig(
                        range_start=(freeze_datetime - timedelta(seconds=30)).isoformat(),
                        range_end=freeze_datetime.isoformat(),
                    )
                }
            ),
        )
        assert result.success
        # There should be runless materializations for the dag asset corresponding to run-dag,
        dag_mat = instance.get_latest_materialization_event(
            make_default_dag_asset_key(instance_name=af_instance.name, dag_id="dag")
        )
        assert dag_mat is not None
        assert dag_mat.run_id == ""

        mapped_asset_mat = instance.get_latest_materialization_event(AssetKey("a"))
        assert mapped_asset_mat is not None
        assert mapped_asset_mat.run_id == ""


def test_monitor_sensor_cursor(init_load_context: None, instance: DagsterInstance) -> None:
    """Test that monitoring job correctly represents state in Dagster."""
    freeze_datetime = datetime(2021, 1, 1, tzinfo=timezone.utc)

    with freeze_time(freeze_datetime):
        defs, af_instance = create_defs_and_instance(
            assets_per_task={
                "dag": {"task": [("a", [])]},
            },
            create_runs=False,
            create_assets_defs=False,
        )
        defs = build_job_based_airflow_defs(
            airflow_instance=af_instance,
            mapped_defs=defs,
        )
        context = build_sensor_context(
            instance=instance,
            repository_def=defs.get_repository_def(),
        )
        result = defs.sensors[0](context)  # type: ignore
        assert isinstance(result, RunRequest)
        assert result.run_config["ops"][monitoring_job_op_name(af_instance)] == {
            "config": {
                "range_start": (freeze_datetime - timedelta(days=1)).isoformat(),
                "range_end": freeze_datetime.isoformat(),
            }
        }
        assert result.tags["range_start"] == (freeze_datetime - timedelta(days=1)).isoformat()
        assert result.tags["range_end"] == freeze_datetime.isoformat()
        # Create an actual run for the monitoring job that is not finished.
        run = instance.create_run_for_job(
            job_def=defs.resolve_job_def(monitoring_job_name(af_instance.name)),
            run_id=make_new_run_id(),
            tags=result.tags,
            status=DagsterRunStatus.STARTED,
            run_config=result.run_config,
        )
        result = defs.sensors[0](context)  # type: ignore
        assert isinstance(result, SkipReason)
        assert "Monitoring job is still running" in result.skip_message  # type: ignore
        # Move the run to a finished state.
        instance.report_dagster_event(
            run_id=run.run_id,
            dagster_event=DagsterEvent(
                event_type_value="PIPELINE_SUCCESS",
                job_name=job_name(af_instance.name),
            ),
        )
    # Move time forward and check that we get a new run request.
    with freeze_time(freeze_datetime + timedelta(seconds=30)):
        result = defs.sensors[0](context)  # type: ignore
        assert isinstance(result, RunRequest)
        assert result.run_config["ops"][monitoring_job_op_name(af_instance)] == {
            "config": {
                "range_start": (freeze_datetime).isoformat(),
                "range_end": (freeze_datetime + timedelta(seconds=30)).isoformat(),
            }
        }


def test_metadata_from_step_output_events() -> None:
    freeze_datetime = datetime(2021, 1, 1, tzinfo=timezone.utc)

    defs, af_instance = create_defs_and_instance(
        assets_per_task={
            "dag": {"task": [("a", [])]},
        },
        create_runs=False,
        create_assets_defs=False,
        seeded_runs=[
            # Have a newly started run.
            make_dag_run(
                dag_id="dag",
                run_id="run-dag",
                start_date=freeze_datetime - timedelta(seconds=30),
                end_date=None,
                state="running",
            ),
        ],
        seeded_task_instances=[
            # Have a newly completed task instance for the newly started run.
            make_task_instance(
                dag_id="dag",
                task_id="task",
                run_id="run-dag",
                start_date=freeze_datetime - timedelta(seconds=30),
                end_date=freeze_datetime,
            ),
        ],
    )
    defs = build_job_based_airflow_defs(
        airflow_instance=af_instance,
        mapped_defs=defs,
    )

    @asset
    def a(context: AssetExecutionContext):
        context.add_output_metadata({"foo": "bar"})

    with instance_for_test() as instance:
        # Simulate a run of the job with step output events.
        result = materialize(
            [a],
            tags={
                DAG_ID_TAG_KEY: "dag",
                DAG_RUN_ID_TAG_KEY: "run-dag",
                TASK_ID_TAG_KEY: "task",
                EXTERNALLY_MANAGED_ASSETS_TAG: "true",
            },
            instance=instance,
        )
        assert result.success
        assert result.get_asset_materialization_events() == []
        assert instance.get_latest_materialization_event(AssetKey("a")) is None

        # Now run the monitoring job. The resulting materialization should have metadata.
        result = definitions_execute_job_in_process(
            defs=defs,
            job_name=monitoring_job_name(af_instance.name),
            instance=instance,
            tags={REPOSITORY_LABEL_TAG: "placeholder"},
            run_config=RunConfig(
                ops={
                    monitoring_job_op_name(af_instance): MonitoringConfig(
                        range_start=(freeze_datetime - timedelta(seconds=30)).isoformat(),
                        range_end=freeze_datetime.isoformat(),
                    )
                }
            ),
        )

        run_record = next(
            iter(
                instance.get_run_records(
                    filters=RunsFilter(
                        tags={DAG_RUN_ID_TAG_KEY: "run-dag", OBSERVATION_RUN_TAG_KEY: "true"}
                    )
                )
            )
        )
        assert run_record.dagster_run.status == DagsterRunStatus.STARTED
        mat = instance.get_latest_materialization_event(AssetKey("a"))
        assert mat is not None
        assert mat.asset_materialization.metadata == {"foo": TextMetadataValue("bar")}  # type: ignore


def test_monitoring_sensor_run_fails(instance: DagsterInstance) -> None:
    """Ensure that sensor does not advance if the monitoring job run fails."""
    freeze_datetime = datetime(2021, 1, 1, tzinfo=timezone.utc)

    with freeze_time(freeze_datetime):
        defs, af_instance = create_defs_and_instance(
            assets_per_task={
                "dag": {"task": [("a", [])]},
            },
            create_runs=False,
            create_assets_defs=False,
        )
        defs = build_job_based_airflow_defs(
            airflow_instance=af_instance,
            mapped_defs=defs,
        )
        context = build_sensor_context(
            instance=instance,
            repository_def=defs.get_repository_def(),
        )
        result = defs.sensors[0](context)  # type: ignore
        assert isinstance(result, RunRequest)
        assert result.run_config["ops"][monitoring_job_op_name(af_instance)] == {
            "config": {
                "range_start": (freeze_datetime - timedelta(days=1)).isoformat(),
                "range_end": freeze_datetime.isoformat(),
            }
        }
        assert result.tags["range_start"] == (freeze_datetime - timedelta(days=1)).isoformat()
        assert result.tags["range_end"] == freeze_datetime.isoformat()
        # Create an actual run for the monitoring job that is failed.
        run = instance.create_run_for_job(
            job_def=defs.resolve_job_def(monitoring_job_name(af_instance.name)),
            run_id=make_new_run_id(),
            tags=result.tags,
            status=DagsterRunStatus.FAILURE,
            run_config=result.run_config,
        )
        with pytest.raises(Exception):
            defs.sensors[0](context)  # type: ignore

        # Create a successful run for the monitoring job within the same run group.
        instance.create_run_for_job(
            job_def=defs.resolve_job_def(monitoring_job_name(af_instance.name)),
            run_id=make_new_run_id(),
            status=DagsterRunStatus.SUCCESS,
            tags={ROOT_RUN_ID_TAG: run.run_id, **run.tags},
            run_config=result.run_config,
        )

    with freeze_time(freeze_datetime + timedelta(seconds=30)):
        # Now, the sensor should advance.
        result = defs.sensors[0](context)  # type: ignore
        assert isinstance(result, RunRequest)
        assert result.run_config["ops"][monitoring_job_op_name(af_instance)] == {
            "config": {
                "range_start": (freeze_datetime).isoformat(),
                "range_end": (freeze_datetime + timedelta(seconds=30)).isoformat(),
            }
        }
