from typing import Tuple

MIGRATED_TAG = "airlift/task_migrated"
DAG_ID_METADATA_KEY = "Dag ID"
AIRFLOW_COUPLING_METADATA_KEY = "airlift/couplings"
AirflowCoupling = Tuple[str, str]
