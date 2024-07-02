from airflow.plugins_manager import AirflowPlugin
from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__ as __version__
from .resources import (
    make_ephemeral_airflow_db_resource as make_ephemeral_airflow_db_resource,
    make_persistent_airflow_db_resource as make_persistent_airflow_db_resource,
)
from .dagster_factory import (
    make_schedules_and_jobs_from_airflow_dag_bag as make_schedules_and_jobs_from_airflow_dag_bag,
    make_dagster_definitions_from_airflow_dag_bag as make_dagster_definitions_from_airflow_dag_bag,
    make_dagster_definitions_from_airflow_dags_path as make_dagster_definitions_from_airflow_dags_path,
    make_dagster_definitions_from_airflow_example_dags as make_dagster_definitions_from_airflow_example_dags,
)
from .hooks.dagster_hook import DagsterHook as DagsterHook
from .links.dagster_link import DagsterLink as DagsterLink
from .dagster_job_factory import (
    make_dagster_job_from_airflow_dag as make_dagster_job_from_airflow_dag,
)
from .dagster_asset_factory import load_assets_from_airflow_dag as load_assets_from_airflow_dag
from .operators.dagster_operator import (
    DagsterOperator as DagsterOperator,
    DagsterCloudOperator as DagsterCloudOperator,
)

DagsterLibraryRegistry.register("dagster-airflow", __version__)

__all__ = [
    "make_dagster_definitions_from_airflow_dags_path",
    "make_dagster_definitions_from_airflow_dag_bag",
    "make_schedules_and_jobs_from_airflow_dag_bag",
    "make_dagster_job_from_airflow_dag",
    "load_assets_from_airflow_dag",
    "make_ephemeral_airflow_db_resource",
    "make_persistent_airflow_db_resource",
    "DagsterHook",
    "DagsterLink",
    "DagsterOperator",
    "DagsterCloudOperator",
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
