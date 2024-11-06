from typing import Any, Mapping, NamedTuple, Optional

TERMINAL_STATI = ["SUCCESS", "FAILURE", "CANCELED"]
SYSTEM_TAG_PREFIX = "dagster/"
MAX_RETRIES_TAG = f"{SYSTEM_TAG_PREFIX}max_retries"
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
    def run_retries_configured(self) -> bool:
        return MAX_RETRIES_TAG in self.tags

    @property
    def has_remaining_retries(self) -> bool:
        if MAX_RETRIES_TAG not in self.tags:
            raise Exception(
                "Tried to retrieve tags from run, but run retries "
                f"were either not set or not properly configured. Found tags: {self.tags}"
            )
        return self.max_retries - self.retry_number > 0

    @property
    def run_will_automatically_retry(self) -> bool:
        if not self.run_retries_configured:
            return False
        if (
            not self.should_retry_on_asset_or_op_failure
            and self.failure_reason == STEP_FAILURE_REASON
        ):
            return False
        return self.has_remaining_retries

    @property
    def should_retry_on_asset_or_op_failure(self) -> bool:
        return get_boolean_tag_value(self.tags.get(RETRY_ON_ASSET_OR_OP_FAILURE_TAG), True)

    @property
    def failure_reason(self) -> Optional[str]:
        return self.tags.get(RUN_FAILURE_REASON_TAG)

    @property
    def retry_number(self) -> int:
        # this is sketchy
        return int(self.tags.get(RETRY_NUMBER_TAG, 0))

    @property
    def success(self) -> bool:
        return self.status == SUCCESS_STATUS

    @property
    def max_retries(self) -> int:
        if MAX_RETRIES_TAG not in self.tags:
            raise Exception("Could not determine max retries by tag because tag is not set.")
        return int(self.tags[MAX_RETRIES_TAG])


def get_boolean_tag_value(tag_value: Optional[str], default_value: bool = False) -> bool:
    if tag_value is None:
        return default_value

    return tag_value.lower() not in {"false", "none", "0", ""}
