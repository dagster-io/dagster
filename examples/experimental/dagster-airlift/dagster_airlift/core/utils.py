from typing import List, Optional, Tuple, cast

from dagster import AssetSpec
from dagster._core.definitions.utils import VALID_NAME_REGEX
from dagster._core.storage.tags import KIND_PREFIX

from dagster_airlift.constants import (
    AIRFLOW_COUPLING_METADATA_KEY,
    DAG_ID_METADATA_KEY,
    AirflowCoupling,
)


def convert_to_valid_dagster_name(name: str) -> str:
    """Converts a name to a valid dagster name by replacing invalid characters with underscores. / is converted to a double underscore."""
    return "".join(c if VALID_NAME_REGEX.match(c) else "__" if c == "/" else "_" for c in name)


def get_couplings_from_spec(spec: AssetSpec) -> Optional[List[Tuple[str, str]]]:
    if AIRFLOW_COUPLING_METADATA_KEY in spec.metadata:
        return cast(List[AirflowCoupling], spec.metadata[AIRFLOW_COUPLING_METADATA_KEY].value)
    return None


def get_dag_id_from_spec(spec: AssetSpec) -> Optional[str]:
    return spec.metadata.get(DAG_ID_METADATA_KEY)


def airflow_kind_dict() -> dict:
    return {f"{KIND_PREFIX}airflow": ""}


def airflow_dag_kind_dict() -> dict:
    return {f"{KIND_PREFIX}airflow": "", f"{KIND_PREFIX}dag": ""}


def airflow_task_kind_dict() -> dict:
    return {f"{KIND_PREFIX}airflow": "", f"{KIND_PREFIX}task": ""}
