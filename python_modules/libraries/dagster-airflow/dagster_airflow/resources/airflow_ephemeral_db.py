import datetime
import importlib
import os
import tempfile
from typing import List, Mapping, Optional

import airflow
import pytz
from airflow.models.connection import Connection
from airflow.models.dag import DAG
from airflow.models.dagrun import DagRun
from airflow.utils import db
from dagster import (
    Array,
    DagsterInvariantViolationError,
    DagsterRun,
    Field,
    InitResourceContext,
    ResourceDefinition,
    _check as check,
)
from dagster._core.instance import AIRFLOW_EXECUTION_DATE_STR
from dateutil.parser import parse

from dagster_airflow.utils import (
    Locker,
    create_airflow_connections,
    is_airflow_2_loaded_in_environment,
    serialize_connections,
)

# pylint: disable=no-name-in-module,import-error
if is_airflow_2_loaded_in_environment():
    from airflow.utils.state import DagRunState
    from airflow.utils.types import DagRunType
else:
    from airflow.utils.state import State

    # pylint: enable=no-name-in-module,import-error


class AirflowEphemeralDatabase:
    """
    A ephemeral Airflow database Dagster resource.

    """

    def __init__(self, airflow_home_path: str, dagster_run: DagsterRun):
        self.airflow_home_path = airflow_home_path
        self.dagster_run = dagster_run

    @staticmethod
    def from_resource_context(context: InitResourceContext) -> "AirflowEphemeralDatabase":
        airflow_home_path = os.path.join(tempfile.gettempdir(), f"dagster_airflow_{context.run_id}")
        # self.context = context
        os.environ["AIRFLOW_HOME"] = airflow_home_path
        os.makedirs(airflow_home_path, exist_ok=True)
        with Locker(airflow_home_path):
            airflow_initialized = os.path.exists(f"{airflow_home_path}/airflow.db")
            # because AIRFLOW_HOME has been overriden airflow needs to be reloaded
            if is_airflow_2_loaded_in_environment():
                importlib.reload(airflow.configuration)
                importlib.reload(airflow.settings)
                importlib.reload(airflow)
            else:
                importlib.reload(airflow)
            if not airflow_initialized:
                db.initdb()
                create_airflow_connections(
                    [Connection(**c) for c in context.resource_config["connections"]]
                )

        return AirflowEphemeralDatabase(
            airflow_home_path=airflow_home_path,
            dagster_run=check.not_none(context.dagster_run, "Context must have run"),
        )

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
            execution_date = parse(execution_date_str)
            execution_date = execution_date.replace(tzinfo=pytz.timezone(dag.timezone.name))
        except ValueError:
            raise DagsterInvariantViolationError(
                'Could not parse execution_date "{execution_date_str}". Please use datetime'
                " format compatible with  dateutil.parser.parse.".format(
                    execution_date_str=execution_date_str,
                )
            )
        except OverflowError:
            raise DagsterInvariantViolationError(
                'Date "{execution_date_str}" exceeds the largest valid C integer on the system.'
                .format(
                    execution_date_str=execution_date_str,
                )
            )
        return execution_date

    def _parse_execution_date_for_asset(
        self, dag: DAG, run_tags: Mapping[str, str]
    ) -> Optional[datetime.datetime]:
        execution_date_str = run_tags.get("dagster/partition")
        if not execution_date_str:
            raise DagsterInvariantViolationError("dagster/partition is not set")
        execution_date = parse(execution_date_str)
        execution_date = execution_date.replace(tzinfo=pytz.timezone(dag.timezone.name))
        return execution_date

    def get_dagrun(self, dag: DAG) -> DagRun:
        airflow_home_path = os.path.join(
            tempfile.gettempdir(), f"dagster_airflow_{self.dagster_run.run_id}"
        )
        os.makedirs(airflow_home_path, exist_ok=True)
        with Locker(airflow_home_path):
            run_tags = self.dagster_run.tags if self.dagster_run else {}
            if AIRFLOW_EXECUTION_DATE_STR in run_tags:
                execution_date = self._parse_execution_date_for_job(dag, run_tags)
            elif "dagster/partition" in run_tags:
                execution_date = self._parse_execution_date_for_asset(dag, run_tags)
            else:
                raise DagsterInvariantViolationError(
                    'Could not find "{AIRFLOW_EXECUTION_DATE_STR}" in tags "{tags}". Please '
                    'add "{AIRFLOW_EXECUTION_DATE_STR}" to tags before executing'.format(
                        AIRFLOW_EXECUTION_DATE_STR=AIRFLOW_EXECUTION_DATE_STR,
                        tags=run_tags,
                    )
                )
            dagrun = dag.get_dagrun(execution_date=execution_date)
            if not dagrun:
                if is_airflow_2_loaded_in_environment():
                    dagrun = dag.create_dagrun(
                        state=DagRunState.RUNNING,
                        execution_date=execution_date,
                        run_type=DagRunType.MANUAL,
                    )
                else:
                    dagrun = dag.create_dagrun(
                        run_id=f"dagster_airflow_run_{execution_date}",
                        state=State.RUNNING,
                        execution_date=execution_date,
                    )
            return dagrun


def make_ephemeral_airflow_db_resource(connections: List[Connection] = []) -> ResourceDefinition:
    """
    Creates a Dagster resource that provides an ephemeral Airflow database.

    Args:
        connections (List[Connection]): List of Airflow Connections to be created in the Airflow DB

    Returns:
        ResourceDefinition: The ephemeral Airflow DB resource

    """
    serialized_connections = serialize_connections(connections)
    airflow_db_resource_def = ResourceDefinition(
        resource_fn=AirflowEphemeralDatabase.from_resource_context,
        config_schema={
            "connections": Field(
                Array(inner_type=dict),
                default_value=serialized_connections,
                is_required=False,
            ),
        },
        description="Ephemeral Airflow DB to be used by dagster-airflow ",
    )
    return airflow_db_resource_def
