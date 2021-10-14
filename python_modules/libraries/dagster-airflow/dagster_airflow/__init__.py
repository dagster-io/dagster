from dagster.core.utils import check_dagster_package_version

from .dagster_pipeline_factory import (
    make_dagster_pipeline_from_airflow_dag,
    make_dagster_repo_from_airflow_dag_bag,
    make_dagster_repo_from_airflow_dags_path,
    make_dagster_repo_from_airflow_example_dags,
)
from .factory import make_airflow_dag, make_airflow_dag_containerized, make_airflow_dag_for_operator
from .version import __version__
from .operators.operator_to_op import operator_to_op

check_dagster_package_version("dagster-airflow", __version__)

__all__ = [
    "make_airflow_dag",
    "make_airflow_dag_for_operator",
    "make_airflow_dag_containerized",
    "make_dagster_pipeline_from_airflow_dag",
    "make_dagster_repo_from_airflow_dags_path",
    "make_dagster_repo_from_airflow_dag_bag",
    "operator_to_op",
]
