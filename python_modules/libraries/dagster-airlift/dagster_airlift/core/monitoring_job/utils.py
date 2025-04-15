from typing import Optional, Union

from dagster._core.execution.context.op_execution_context import OpExecutionContext
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster_airlift.constants import DAG_ID_TAG_KEY, DAG_RUN_ID_TAG_KEY
from dagster_airlift.core.runtime_representations import DagRun, TaskInstance

START_LOOKBACK_SECONDS = 60  # Lookback one minute in time for the initial setting of the cursor.


def get_range_from_run_history(
    context: OpExecutionContext, effective_ts: float
) -> tuple[float, float]:
    prev_run = next(
        iter(
            context.instance.get_runs(
                filters=RunsFilter(job_name=context.job_name, statuses=[DagsterRunStatus.SUCCESS]),
                limit=1,
            )
        ),
        None,
    )
    if prev_run:
        # Start from the end of the last run
        range_start = float(prev_run.tags_for_storage()["dagster-airlift/monitoring_job_range_end"])
    else:
        range_start = effective_ts - START_LOOKBACK_SECONDS
    range_end = effective_ts
    return range_start, range_end


def augment_monitor_run_with_range_tags(
    context: OpExecutionContext, range_start: float, range_end: float
) -> None:
    context.instance.add_run_tags(
        run_id=context.run_id,
        new_tags={
            "dagster-airlift/monitoring_job_range_start": str(range_start),
            "dagster-airlift/monitoring_job_range_end": str(range_end),
        },
    )


def structured_log(context: OpExecutionContext, message: str) -> None:
    context.log.info(f"[Airflow Monitoring Job]: {message}")


def get_dagster_run_for_airflow_repr(
    context: OpExecutionContext, airflow_repr: Union[DagRun, TaskInstance]
) -> Optional[DagsterRun]:
    return next(
        iter(
            context.instance.get_runs(
                filters=RunsFilter(
                    tags={
                        DAG_RUN_ID_TAG_KEY: airflow_repr.run_id,
                        DAG_ID_TAG_KEY: airflow_repr.dag_id,
                    }
                ),
            )
        ),
        None,
    )
