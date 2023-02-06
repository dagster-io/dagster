from airflow.plugins_manager import AirflowPlugin
from dagster._core.utils import check_dagster_package_version

from .dagster_asset_factory import (
    load_assets_from_airflow_dag as load_assets_from_airflow_dag,
)
from .dagster_factory import (
    make_dagster_definitions_from_airflow_dag_bag as make_dagster_definitions_from_airflow_dag_bag,
    make_dagster_definitions_from_airflow_dags_path as make_dagster_definitions_from_airflow_dags_path,
    make_dagster_definitions_from_airflow_example_dags as make_dagster_definitions_from_airflow_example_dags,
    make_schedules_and_jobs_from_airflow_dag_bag as make_schedules_and_jobs_from_airflow_dag_bag,
)
from .dagster_job_factory import (
    make_dagster_job_from_airflow_dag as make_dagster_job_from_airflow_dag,
)
from .hooks.dagster_hook import DagsterHook as DagsterHook
from .links.dagster_link import DagsterLink as DagsterLink
from .operators.dagster_operator import (
    DagsterCloudOperator as DagsterCloudOperator,
    DagsterOperator as DagsterOperator,
)
from .version import __version__ as __version__

check_dagster_package_version("dagster-airflow", __version__)

__all__ = [
    "make_dagster_definitions_from_airflow_dags_path",
    "make_dagster_definitions_from_airflow_dag_bag",
    "make_schedules_and_jobs_from_airflow_dag_bag",
    "make_dagster_job_from_airflow_dag",
    "load_assets_from_airflow_dag",
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


def get_provider_info():
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
