from dagster._core.definitions.definitions_class import Definitions
from dagster_airlift.core.load_defs import build_full_automapped_dags_from_airflow_instance

from .airflow_instance import local_airflow_instance


def build_automapped_defs() -> Definitions:
    return build_full_automapped_dags_from_airflow_instance(
        airflow_instance=local_airflow_instance(),
    )


defs = build_automapped_defs()
