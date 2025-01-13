from collections.abc import Mapping
from typing import Any, NamedTuple, Optional

# These constants exist within the Dagster main package, but are duplicated here to avoid taking a dependency on Dagster within
# the dagster-airlift[in-airflow] submodule.
TERMINAL_STATI = ["SUCCESS", "FAILURE", "CANCELED"]
SYSTEM_TAG_PREFIX = "dagster/"
MAX_RETRIES_TAG = f"{SYSTEM_TAG_PREFIX}max_retries"
WILL_RETRY_TAG = f"{SYSTEM_TAG_PREFIX}will_retry"
AUTO_RETRY_RUN_ID_TAG = f"{SYSTEM_TAG_PREFIX}auto_retry_run_id"
RETRY_NUMBER_TAG = f"{SYSTEM_TAG_PREFIX}retry_number"
PARENT_RUN_ID_TAG = f"{SYSTEM_TAG_PREFIX}parent_run_id"
SUCCESS_STATUS = "SUCCESS"
RETRY_ON_ASSET_OR_OP_FAILURE_TAG = f"{SYSTEM_TAG_PREFIX}retry_on_asset_or_op_failure"
RUN_FAILURE_REASON_TAG = f"{SYSTEM_TAG_PREFIX}failure_reason"
STEP_FAILURE_REASON = "STEP_FAILURE"


class DagsterRunResult(NamedTuple):
    status: str
    tags: Mapping[str, Any]

    @property
    def run_will_automatically_retry(self) -> bool:
        return (
            not self.succeeded
            and get_boolean_tag_value(self.tags.get(WILL_RETRY_TAG), False) is True
        )

    @property
    def retried_run_id(self) -> Optional[str]:
        return self.tags.get(AUTO_RETRY_RUN_ID_TAG)

    @property
    def succeeded(self) -> bool:
        return self.status == SUCCESS_STATUS


def get_boolean_tag_value(tag_value: Optional[str], default_value: bool = False) -> bool:
    if tag_value is None:
        return default_value

    return tag_value.lower() not in {"false", "none", "0", ""}
