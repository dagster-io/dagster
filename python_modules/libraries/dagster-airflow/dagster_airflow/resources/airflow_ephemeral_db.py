import importlib
import os
import tempfile
from typing import List, Optional

import airflow
from airflow.models.connection import Connection
from airflow.utils import db
from dagster import (
    Array,
    DagsterRun,
    Field,
    InitResourceContext,
    Noneable,
    ResourceDefinition,
    _check as check,
)

from dagster_airflow.resources.airflow_db import AirflowDatabase
from dagster_airflow.utils import (
    Locker,
    create_airflow_connections,
    is_airflow_2_loaded_in_environment,
    serialize_connections,
)


class AirflowEphemeralDatabase(AirflowDatabase):
    """A ephemeral Airflow database Dagster resource."""

    def __init__(
        self, airflow_home_path: str, dagster_run: DagsterRun, dag_run_config: Optional[dict] = None
    ):
        self.airflow_home_path = airflow_home_path
        super().__init__(dagster_run=dagster_run, dag_run_config=dag_run_config)

    @staticmethod
    def _initialize_database(
        airflow_home_path: str = os.path.join(tempfile.gettempdir(), "dagster_airflow"),
        connections: List[Connection] = [],
    ):
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
                create_airflow_connections(connections)

    @staticmethod
    def from_resource_context(context: InitResourceContext) -> "AirflowEphemeralDatabase":
        airflow_home_path = os.path.join(tempfile.gettempdir(), f"dagster_airflow_{context.run_id}")
        AirflowEphemeralDatabase._initialize_database(
            airflow_home_path=airflow_home_path,
            connections=[Connection(**c) for c in context.resource_config["connections"]],
        )
        return AirflowEphemeralDatabase(
            airflow_home_path=airflow_home_path,
            dagster_run=check.not_none(context.dagster_run, "Context must have run"),
            dag_run_config=context.resource_config.get("dag_run_config"),
        )


def make_ephemeral_airflow_db_resource(
    connections: List[Connection] = [], dag_run_config: Optional[dict] = None
) -> ResourceDefinition:
    """Creates a Dagster resource that provides an ephemeral Airflow database.

    Args:
        connections (List[Connection]): List of Airflow Connections to be created in the Airflow DB
        dag_run_config (Optional[dict]): dag_run configuration to be used when creating a DagRun

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
            "dag_run_config": Field(
                Noneable(dict),
                default_value=dag_run_config,
                is_required=False,
            ),
        },
        description="Ephemeral Airflow DB to be used by dagster-airflow ",
    )
    return airflow_db_resource_def
