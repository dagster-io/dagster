import os
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from dagster_shared.record import as_dict

if TYPE_CHECKING:
    from dagster._core.storage.dagster_run import DagsterRun

# 'airflow_execution_date' and 'is_airflow_ingest_pipeline' are hardcoded tags used in the
# airflow ingestion logic (see: dagster_pipeline_factory.py). 'airflow_execution_date' stores the
# 'execution_date' used in Airflow operator execution and 'is_airflow_ingest_pipeline' determines
# whether 'airflow_execution_date' is needed.
# https://github.com/dagster-io/dagster/issues/2403
AIRFLOW_EXECUTION_DATE_STR = "airflow_execution_date"
IS_AIRFLOW_INGEST_PIPELINE_STR = "is_airflow_ingest_pipeline"

# Our internal guts can handle empty strings for job name and run id
# However making these named constants for documentation, to encode where we are making the assumption,
# and to allow us to change this more easily in the future, provided we are disciplined about
# actually using this constants.
RUNLESS_RUN_ID = ""
RUNLESS_JOB_NAME = ""


# The DAGSTER_EVENT_BATCH_SIZE env var controls whether we store events in batches. When enabled,
# this causes _dagster_event_batch_metadata to be injected into log records, and we will then use
# the store_event_batch method of EventLogStorage to persist a batch of events at once instead of
# calling store_event individually. This is expected for cloud deployments, but should only have a
# minimal impact for OSS since the batch is sent over a thread queue.
#
# When the batch size is set to 0, we bypass the batching mechanism almost
# entirely (multiple store_event calls are made instead of store_event_batch). This makes batching
# opt-in.
#
# Note that we don't store the value in the constant so that it can be changed without a process
# restart.
def _get_event_batch_size() -> int:
    return int(os.getenv("DAGSTER_EVENT_BATCH_SIZE", "0"))


def _is_batch_writing_enabled() -> bool:
    return _get_event_batch_size() > 0


def _check_run_equality(
    pipeline_run: "DagsterRun", candidate_run: "DagsterRun"
) -> Mapping[str, tuple[Any, Any]]:
    field_diff: dict[str, tuple[Any, Any]] = {}
    for field, expected_value in as_dict(pipeline_run):
        candidate_value = getattr(candidate_run, field)
        if expected_value != candidate_value:
            field_diff[field] = (expected_value, candidate_value)

    return field_diff


def _format_field_diff(field_diff: Mapping[str, tuple[Any, Any]]) -> str:
    return "\n".join(
        [
            (
                "    {field_name}:\n"
                + "        Expected: {expected_value}\n"
                + "        Received: {candidate_value}"
            ).format(
                field_name=field_name,
                expected_value=expected_value,
                candidate_value=candidate_value,
            )
            for field_name, (
                expected_value,
                candidate_value,
            ) in field_diff.items()
        ]
    )
