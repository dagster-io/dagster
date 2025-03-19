import logging

import dagster as dg
from dagster._core.remote_representation.origin import (
    ManagedGrpcPythonEnvCodeLocationOrigin,
    RemoteJobOrigin,
    RemoteRepositoryOrigin,
)
from dagster._core.storage.tags import REPOSITORY_LABEL_TAG
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.utils import make_new_run_id
from dagster_airlift.core.job_builder import (
    build_job_from_airflow_dag,
    build_observation_job_sensor,
)

from kitchen_sink.airflow_instance import local_airflow_instance


def build_defs_from_airflow_instance_v2(af_instance) -> dg.Definitions:
    af_instance = local_airflow_instance()
    dag_ids_to_build = [dag.dag_id for dag in af_instance.list_dags()]
    jobs = []
    assets = []
    for dag_id in dag_ids_to_build:
        job, addl_assets = build_job_from_airflow_dag(
            airflow_instance=af_instance,
            dag_id=dag_id,
            mapped_assets=[],
        )
        jobs.append(job)
        assets.extend(addl_assets)
    sensor = build_observation_job_sensor(
        jobs=jobs,
        airflow_instance=local_airflow_instance(),
    )

    return dg.Definitions(
        sensors=[sensor],
        jobs=jobs,
        assets=assets,
    )


def migrate_runs():
    af_instance = local_airflow_instance()
    dag_ids_to_build = [dag.dag_id for dag in af_instance.list_dags()]
    instance = dg.DagsterInstance.get()
    runs, _ = af_instance.get_dag_runs_batch(dag_ids_to_build, states=["success", "failed"])
    for run in runs:
        expected_tag = {"airflow/run_id": run.run_id}
        if instance.get_runs(filters=dg.RunsFilter(tags=expected_tag)):
            continue
        else:
            run_id = make_new_run_id()
            instance.add_run(
                dg.DagsterRun(
                    job_name=run.dag_id,
                    run_id=run_id,
                    # Hack to get runs to show up on pages.
                    tags={
                        "airflow/run_id": run.run_id,
                        REPOSITORY_LABEL_TAG: "__repository__@kitchen_sink.dagster_defs.jobs",
                    },
                    status=dg.DagsterRunStatus.STARTING
                    if run.state == "success"
                    else dg.DagsterRunStatus.FAILURE,
                    remote_job_origin=RemoteJobOrigin(
                        repository_origin=RemoteRepositoryOrigin(
                            code_location_origin=ManagedGrpcPythonEnvCodeLocationOrigin(
                                loadable_target_origin=LoadableTargetOrigin(
                                    module_name="kitchen_sink.dagster_defs.jobs",
                                )
                            ),
                            repository_name="__repository__",
                        ),
                        job_name=run.dag_id,
                    ),
                )
            )
            instance.handle_new_event(
                dg.EventLogEntry(
                    dagster_event=dg.DagsterEvent(
                        event_type_value=dg.DagsterEventType.RUN_START.value,
                        job_name=run.dag_id,
                    ),
                    run_id=run_id,
                    error_info=None,
                    timestamp=run.start_date.timestamp(),
                    user_message="",
                    level=logging.INFO,
                )
            )
            instance.handle_new_event(
                dg.EventLogEntry(
                    dagster_event=dg.DagsterEvent(
                        event_type_value=dg.DagsterEventType.RUN_SUCCESS.value
                        if run.state == "success"
                        else dg.DagsterEventType.RUN_FAILURE.value,
                        job_name=run.dag_id,
                    ),
                    run_id=run_id,
                    error_info=None,
                    timestamp=run.end_date.timestamp(),
                    user_message="",
                    level=logging.INFO,
                )
            )
