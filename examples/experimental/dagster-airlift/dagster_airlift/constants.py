from typing import Tuple

PKG_PREFIX = "dagster-airlift/"
MIGRATED_TAG = f"{PKG_PREFIX}task_migrated"
DAG_ID_METADATA_KEY = f"{PKG_PREFIX}/dag_id"
AIRFLOW_COUPLING_METADATA_KEY = f"{PKG_PREFIX}couplings"
AirflowCoupling = Tuple[str, str]
