import datetime
from collections.abc import Mapping
from typing import Optional

import pendulum
from airflow.models.dag import DAG
from airflow.models.dagrun import DagRun
from dagster import (
    DagsterInvariantViolationError,
    DagsterRun,
    _check as check,
)
from dagster._core.instance import AIRFLOW_EXECUTION_DATE_STR

from dagster_airflow.utils import is_airflow_2_loaded_in_environment

if is_airflow_2_loaded_in_environment():
    from airflow.utils.state import DagRunState
    from airflow.utils.types import DagRunType
else:
    from airflow.utils.state import State


class AirflowDatabase:
    """Airflow database Dagster resource."""

    def __init__(self, dagster_run: DagsterRun, dag_run_config: Optional[dict] = None):
        self.dagster_run = dagster_run
        self.dag_run_config = dag_run_config

    def _parse_execution_date_for_job(
        self, dag: DAG, run_tags: Mapping[str, str]
    ) -> Optional[datetime.datetime]:
        execution_date_str = run_tags.get(AIRFLOW_EXECUTION_DATE_STR)
        if not execution_date_str:
            raise DagsterInvariantViolationError(
                "Expected execution_date_str to be set in run tags."
            )
        check.str_param(execution_date_str, "execution_date_str")
        try:
            execution_date = pendulum.parse(
                execution_date_str, tz=pendulum.timezone(dag.timezone.name)
            )
        except ValueError:
            raise DagsterInvariantViolationError(
                f'Could not parse execution_date "{execution_date_str}". Please use datetime'
                " format compatible with  dateutil.parser.parse."
            )
        except OverflowError:
            raise DagsterInvariantViolationError(
                f'Date "{execution_date_str}" exceeds the largest valid C integer on the system.'
            )
        return execution_date  # pyright: ignore[reportReturnType]

    def _parse_execution_date_for_asset(
        self, dag: DAG, run_tags: Mapping[str, str]
    ) -> Optional[datetime.datetime]:
        execution_date_str = run_tags.get("dagster/partition")
        if not execution_date_str:
            raise DagsterInvariantViolationError("dagster/partition is not set")
        execution_date = pendulum.parse(execution_date_str, tz=pendulum.timezone(dag.timezone.name))
        return execution_date  # pyright: ignore[reportReturnType]

    def get_dagrun(self, dag: DAG) -> DagRun:
        run_tags = self.dagster_run.tags if self.dagster_run else {}
        if AIRFLOW_EXECUTION_DATE_STR in run_tags:
            execution_date = self._parse_execution_date_for_job(dag, run_tags)
        elif "dagster/partition" in run_tags:
            execution_date = self._parse_execution_date_for_asset(dag, run_tags)
        else:
            raise DagsterInvariantViolationError(
                f'Could not find "{AIRFLOW_EXECUTION_DATE_STR}" in tags "{run_tags}". Please '
                f'add "{AIRFLOW_EXECUTION_DATE_STR}" to tags before executing'
            )
        dagrun = dag.get_dagrun(execution_date=execution_date)
        if not dagrun:
            if is_airflow_2_loaded_in_environment():
                dagrun = dag.create_dagrun(
                    state=DagRunState.RUNNING,  # pyright: ignore[reportPossiblyUnboundVariable]
                    execution_date=execution_date,
                    run_type=DagRunType.MANUAL,  # pyright: ignore[reportPossiblyUnboundVariable]
                    conf=self.dag_run_config,
                )
            else:
                dagrun = dag.create_dagrun(
                    run_id=f"dagster_airflow_run_{execution_date}",
                    state=State.RUNNING,  # type: ignore
                    execution_date=execution_date,
                    conf=self.dag_run_config,
                )
        return dagrun
