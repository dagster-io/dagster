from enum import Enum

PEERED_DAG_MAPPING_METADATA_KEY = "dagster-airlift/peered-dag-mapping"
DAG_MAPPING_METADATA_KEY = "dagster-airlift/dag-mapping"
AIRFLOW_SOURCE_METADATA_KEY_PREFIX = "dagster-airlift/source"
TASK_MAPPING_METADATA_KEY = "dagster-airlift/task-mapping"
AUTOMAPPED_TASK_METADATA_KEY = "dagster-airlift/automapped-task"
# This represents the timestamp used in ordering the materializatons.
EFFECTIVE_TIMESTAMP_METADATA_KEY = "dagster-airlift/effective-timestamp"
AIRFLOW_TASK_INSTANCE_LOGICAL_DATE_METADATA_KEY = (
    "dagster-airlift/airflow-task-instance-logical-date"
)
AIRFLOW_RUN_ID_METADATA_KEY = "dagster-airlift/airflow-run-id"
DAG_RUN_ID_TAG_KEY = "dagster-airlift/airflow-dag-run-id"
DAG_ID_TAG_KEY = "dagster-airlift/airflow-dag-id"
TASK_ID_TAG_KEY = "dagster-airlift/airflow-task-id"
DAG_RUN_URL_TAG_KEY = "dagster-airlift/airflow-dag-run-url"
OBSERVATION_RUN_TAG_KEY = "dagster-airlift/observation-run"

DEFER_ASSET_EVENTS_TAG = "dagster/defer_asset_events"

SOURCE_CODE_METADATA_KEY = "Source Code"

NO_STEP_KEY = "__no_step__"


class AirflowVersion(Enum):
    AIRFLOW_2 = "2"
    AIRFLOW_3 = "3"

    @property
    def api_version(self) -> str:
        return "v1" if self == AirflowVersion.AIRFLOW_2 else "v2"


def infer_af_version_from_env() -> "AirflowVersion":
    try:
        import airflow

        version = airflow.__version__
        if version.startswith("2."):
            return AirflowVersion.AIRFLOW_2
        elif version.startswith("3."):
            return AirflowVersion.AIRFLOW_3
    except ImportError:
        raise ValueError(
            "Airflow is not installed - could not infer Airflow version from environment."
        )
