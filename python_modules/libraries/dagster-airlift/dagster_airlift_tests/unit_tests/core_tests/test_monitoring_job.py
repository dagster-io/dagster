from datetime import datetime, timedelta, timezone

import dagster._check as check
from dagster import AssetKey, DagsterInstance
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import REPOSITORY_LABEL_TAG
from dagster._core.test_utils import freeze_time
from dagster._core.utils import make_new_run_id
from dagster_airlift.constants import DAG_ID_TAG_KEY, DAG_RUN_ID_TAG_KEY
from dagster_airlift.core.job_builder import job_name
from dagster_airlift.core.load_defs import (
    build_defs_from_airflow_instance,
    build_job_based_airflow_defs,
)
from dagster_airlift.core.monitoring_job.builder import build_airflow_monitoring_defs
from dagster_airlift.core.serialization.defs_construction import make_default_dag_asset_key
from dagster_airlift.core.utils import monitoring_job_name
from dagster_airlift.test import make_dag_run, make_task_instance

from dagster_airlift_tests.unit_tests.conftest import create_defs_and_instance


def make_dag_key(dag_id: str) -> AssetKey:
    return AssetKey(["test_instance", "dag", dag_id])


def make_dag_key_str(dag_id: str) -> str:
    return make_dag_key(dag_id).to_user_string()


def test_monitoring_job_execution(init_load_context: None, instance: DagsterInstance) -> None:
    """Test that monitoring job correctly represents state in Dagster."""
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
        success_dagster_run_id = make_new_run_id()
        instance.add_run(
            DagsterRun(
                job_name=job_name("dag"),
                run_id=success_dagster_run_id,
                tags={
                    DAG_RUN_ID_TAG_KEY: "success-run",
                    DAG_ID_TAG_KEY: "dag",
                },
                status=DagsterRunStatus.STARTED,
            )
        )
        failure_dagster_run_id = make_new_run_id()
        instance.add_run(
            DagsterRun(
                job_name=job_name("dag"),
                run_id=failure_dagster_run_id,
                tags={
                    DAG_RUN_ID_TAG_KEY: "failure-run",
                    DAG_ID_TAG_KEY: "dag",
                },
                status=DagsterRunStatus.STARTED,
            )
        )
        result = defs.execute_job_in_process(
            job_name=monitoring_job_name(af_instance.name),
            instance=instance,
            tags={REPOSITORY_LABEL_TAG: "placeholder"},
        )
        assert result.success

        # Expect that the success and failure runs are marked as finished.
        assert (
            check.not_none(instance.get_run_by_id(success_dagster_run_id)).status
            == DagsterRunStatus.SUCCESS
        )
        assert (
            check.not_none(instance.get_run_by_id(failure_dagster_run_id)).status
            == DagsterRunStatus.FAILURE
        )
        # Expect that we created a new run for the newly running run.
        newly_started_run = next(
            iter(instance.get_runs(filters=RunsFilter(tags={DAG_RUN_ID_TAG_KEY: "run-dag"})))
        )

        assert newly_started_run.status == DagsterRunStatus.STARTED

        # There should be planned materialization data for the task.
        planned_info = instance.get_latest_planned_materialization_info(AssetKey("a"))
        assert planned_info
        assert planned_info.run_id == newly_started_run.run_id
        # Expect that we emitted asset materialization events for the task.
        mapped_asset_mat = instance.get_latest_materialization_event(AssetKey("a"))
        assert mapped_asset_mat is not None
        assert mapped_asset_mat.run_id == newly_started_run.run_id


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
        result = full_defs.execute_job_in_process(
            job_name=monitoring_job_name(af_instance.name),
            instance=instance,
            tags={REPOSITORY_LABEL_TAG: "placeholder"},
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
