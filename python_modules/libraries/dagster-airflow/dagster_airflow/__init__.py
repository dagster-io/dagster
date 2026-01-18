from airflow.plugins_manager import AirflowPlugin
from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_airflow.dagster_asset_factory import (
    load_assets_from_airflow_dag as load_assets_from_airflow_dag,
)
from dagster_airflow.dagster_factory import (
    make_dagster_definitions_from_airflow_dag_bag as make_dagster_definitions_from_airflow_dag_bag,
    make_dagster_definitions_from_airflow_dags_path as make_dagster_definitions_from_airflow_dags_path,
    make_dagster_definitions_from_airflow_example_dags as make_dagster_definitions_from_airflow_example_dags,
    make_schedules_and_jobs_from_airflow_dag_bag as make_schedules_and_jobs_from_airflow_dag_bag,
)
from dagster_airflow.dagster_job_factory import (
    make_dagster_job_from_airflow_dag as make_dagster_job_from_airflow_dag,
)
from dagster_airflow.hooks.dagster_hook import DagsterHook as DagsterHook
from dagster_airflow.links.dagster_link import DagsterLink as DagsterLink
from dagster_airflow.operators.dagster_operator import (
    DagsterCloudOperator as DagsterCloudOperator,
    DagsterOperator as DagsterOperator,
)
from dagster_airflow.resources import (
    make_ephemeral_airflow_db_resource as make_ephemeral_airflow_db_resource,
    make_persistent_airflow_db_resource as make_persistent_airflow_db_resource,
)
from dagster_airflow.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-airflow", __version__)

__all__ = [
    "DagsterCloudOperator",
    "DagsterHook",
    "DagsterLink",
    "DagsterOperator",
    "load_assets_from_airflow_dag",
    "make_dagster_definitions_from_airflow_dag_bag",
    "make_dagster_definitions_from_airflow_dags_path",
    "make_dagster_job_from_airflow_dag",
    "make_ephemeral_airflow_db_resource",
    "make_persistent_airflow_db_resource",
    "make_schedules_and_jobs_from_airflow_dag_bag",
]


class DagsterAirflowPlugin(AirflowPlugin):
    name = "dagster_airflow"
    hooks = [DagsterHook]
    operators = [DagsterOperator, DagsterCloudOperator]
    operator_extra_links = [
        DagsterLink(),
    ]


def get_provider_info() -> dict:
    return {
        "package-name": "dagster-airflow",
        "name": "Dagster Airflow",
        "description": "`Dagster <https://docs.dagster.io>`__",
        "hook-class-names": ["dagster_airflow.hooks.dagster_hook.DagsterHook"],
        "connection-types": [
            {
                "connection-type": "dagster",
                "hook-class-name": "dagster_airflow.hooks.dagster_hook.DagsterHook",
            }
        ],
        "versions": [__version__],
    }
