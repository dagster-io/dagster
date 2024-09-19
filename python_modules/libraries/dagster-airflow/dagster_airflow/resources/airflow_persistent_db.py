import importlib
import os
from typing import List, Optional

import airflow
from airflow.models.connection import Connection
from dagster import (
    Array,
    DagsterRun,
    Field,
    InitResourceContext,
    ResourceDefinition,
    StringSource,
    _check as check,
)

from dagster_airflow.resources.airflow_db import AirflowDatabase
from dagster_airflow.utils import (
    create_airflow_connections,
    is_airflow_2_loaded_in_environment,
    serialize_connections,
)


class AirflowPersistentDatabase(AirflowDatabase):
    """A persistent Airflow database Dagster resource."""

    def __init__(self, dagster_run: DagsterRun, uri: str, dag_run_config: Optional[dict] = None):
        self.uri = uri
        super().__init__(dagster_run=dagster_run, dag_run_config=dag_run_config)

    @staticmethod
    def _initialize_database(uri: str, connections: List[Connection] = []):
        if is_airflow_2_loaded_in_environment("2.3.0"):
            os.environ["AIRFLOW__DATABASE__SQL_ALCHEMY_CONN"] = uri
            importlib.reload(airflow.configuration)
            importlib.reload(airflow.settings)
            importlib.reload(airflow)
        else:
            os.environ["AIRFLOW__CORE__SQL_ALCHEMY_CONN"] = uri
            importlib.reload(airflow)
        create_airflow_connections(connections)

    @staticmethod
    def from_resource_context(context: InitResourceContext) -> "AirflowPersistentDatabase":
        uri = context.resource_config["uri"]
        AirflowPersistentDatabase._initialize_database(
            uri=uri, connections=[Connection(**c) for c in context.resource_config["connections"]]
        )
        return AirflowPersistentDatabase(
            dagster_run=check.not_none(context.dagster_run, "Context must have run"),
            uri=uri,
            dag_run_config=context.resource_config["dag_run_config"],
        )


def make_persistent_airflow_db_resource(
    uri: str = "",
    connections: List[Connection] = [],
    dag_run_config: Optional[dict] = {},
) -> ResourceDefinition:
    """Creates a Dagster resource that provides an persistent Airflow database.


    Usage:
        .. code-block:: python

            from dagster_airflow import (
                make_dagster_definitions_from_airflow_dags_path,
                make_persistent_airflow_db_resource,
            )
            postgres_airflow_db = "postgresql+psycopg2://airflow:airflow@localhost:5432/airflow"
            airflow_db = make_persistent_airflow_db_resource(uri=postgres_airflow_db)
            definitions = make_dagster_definitions_from_airflow_example_dags(
                '/path/to/dags/',
                resource_defs={"airflow_db": airflow_db}
            )


    Args:
        uri: SQLAlchemy URI of the Airflow DB to be used
        connections (List[Connection]): List of Airflow Connections to be created in the Airflow DB
        dag_run_config (Optional[dict]): dag_run configuration to be used when creating a DagRun

    Returns:
        ResourceDefinition: The persistent Airflow DB resource

    """
    if is_airflow_2_loaded_in_environment():
        os.environ["AIRFLOW__DATABASE__SQL_ALCHEMY_CONN"] = uri
    else:
        os.environ["AIRFLOW__CORE__SQL_ALCHEMY_CONN"] = uri

    serialized_connections = serialize_connections(connections)

    airflow_db_resource_def = ResourceDefinition(
        resource_fn=AirflowPersistentDatabase.from_resource_context,
        config_schema={
            "uri": Field(
                StringSource,
                default_value=uri,
                is_required=False,
            ),
            "connections": Field(
                Array(inner_type=dict),
                default_value=serialized_connections,
                is_required=False,
            ),
            "dag_run_config": Field(
                dict,
                default_value=dag_run_config,
                is_required=False,
            ),
        },
        description="Persistent Airflow DB to be used by dagster-airflow ",
    )
    return airflow_db_resource_def
