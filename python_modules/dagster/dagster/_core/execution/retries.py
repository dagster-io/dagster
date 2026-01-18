import warnings
from collections import defaultdict
from collections.abc import Mapping
from enum import Enum
from typing import TYPE_CHECKING, Optional

from dagster_shared.serdes import whitelist_for_serdes

import dagster._check as check
from dagster._config.field import Field
from dagster._config.field_utils import Selector
from dagster._core.errors import DagsterRunNotFoundError
from dagster._core.storage.tags import MAX_RETRIES_TAG, RETRY_ON_ASSET_OR_OP_FAILURE_TAG
from dagster._utils.tags import get_boolean_tag_value

if TYPE_CHECKING:
    from dagster._core.events import RunFailureReason
    from dagster._core.instance import DagsterInstance
    from dagster._core.storage.dagster_run import DagsterRun


def get_retries_config():
    return Field(
        Selector({"enabled": {}, "disabled": {}}),
        default_value={"enabled": {}},
        description="Whether retries are enabled or not. By default, retries are enabled.",
    )


@whitelist_for_serdes
class RetryMode(Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    # Designed for use of inner plan execution within "orchestrator" engine such as multiprocess,
    # up_for_retry steps are not directly re-enqueued, deferring that to the engine.
    DEFERRED = "deferred"

    @staticmethod
    def from_config(config_value: Mapping[str, Mapping]) -> Optional["RetryMode"]:
        for selector in config_value.keys():
            return RetryMode(selector)
        return None

    @property
    def enabled(self) -> bool:
        return self == RetryMode.ENABLED

    @property
    def disabled(self) -> bool:
        return self == RetryMode.DISABLED

    @property
    def deferred(self) -> bool:
        return self == RetryMode.DEFERRED

    def for_inner_plan(self) -> "RetryMode":
        if self.disabled or self.deferred:
            return self
        elif self.enabled:
            return RetryMode.DEFERRED
        else:
            check.failed("Unexpected RetryMode! Expected enabled, disabled, or deferred")


class RetryState:
    def __init__(self, previous_attempts: Optional[Mapping[str, int]] = None):
        self._attempts = defaultdict(int)
        for key, val in check.opt_mapping_param(
            previous_attempts, "previous_attempts", key_type=str, value_type=int
        ).items():
            self._attempts[key] = val

    def get_attempt_count(self, key: str) -> int:
        return self._attempts[key]

    def mark_attempt(self, key: str) -> None:
        self._attempts[key] += 1

    def snapshot_attempts(self) -> Mapping[str, int]:
        return dict(self._attempts)


def auto_reexecution_should_retry_run(
    instance: "DagsterInstance", run: "DagsterRun", run_failure_reason: Optional["RunFailureReason"]
):
    """Determines if a run will be retried by the automatic reexcution system.
    A run will retry if:
    - it is failed.
    - the number of max allowed retries is > 0 (max retries can be set via system setting or run tag).
    - there have not already been >= max_retries retries for the run.

    If the run failure reason was a step failure and the retry_on_asset_or_op_failure tag/system setting is set to false,
    a warning message will be logged and the run will not be retried.

    We determine how many retries have been launched for the run by looking at the size of the run group
    (the set of runs that have the same root_run_id and the run with root_run_id). Since manually launched retries are
    part of the run group, this means that if a user launches a manual retry of run A and then this function
    is called because a retry for run A launched by the auto-reexecution system failed, the manual retry will be
    counted toward max_retries.

    It is unlikely, but possible, that one "extra" retry will be launched by the automatic reexecution system
    since manual retries could be happening in parallel with automatic retries. Here is
    an illustrative example:
    - Max retries is 3
    - Run A fails
    - The automatic reexecution system launches a retry of run A (A_1), which fails
    - The automatic reexecution system launches a retry run A_1 (A_2), which fails
    - This function is executing and has fetched the run_group for run A_2: (A, A_1, A_2)
    - A user launches a manual retry of run A (A_m). The run group is now (A, A_1, A_2, A_m), but this function does
    not have the updated run group
    - Since the run group we've fetched is (A, A_1, A_2), this function will mark A_2 as `will_retry=true` and
    run `A_3` will be launched. This is the "extra" retry, since usually manual retries are counted toward max_retries, but
    in this case it was not.

    We think this is an acceptable tradeoff to make since the automatic reexecution system won't launch more than max_retries
    run itself, just that max_retries + 1 runs could be launched in total if a manual retry is timed to cause this condition (unlikely).
    """
    from dagster._core.events import RunFailureReason
    from dagster._core.storage.dagster_run import DagsterRunStatus

    if run.status != DagsterRunStatus.FAILURE:
        return False

    retry_on_asset_or_op_failure = get_boolean_tag_value(
        run.tags.get(RETRY_ON_ASSET_OR_OP_FAILURE_TAG),
        default_value=instance.run_retries_retry_on_asset_or_op_failure,
    )
    if run_failure_reason == RunFailureReason.STEP_FAILURE and not retry_on_asset_or_op_failure:
        return False

    raw_max_retries_tag = run.tags.get(MAX_RETRIES_TAG)
    if raw_max_retries_tag is None:
        max_retries = instance.run_retries_max_retries
    else:
        try:
            max_retries = int(raw_max_retries_tag)
        except ValueError:
            warnings.warn(f"Error parsing int from tag {MAX_RETRIES_TAG}, won't retry the run.")
            return False
    if max_retries > 0:
        try:
            run_group = instance.get_run_group(run.run_id)
        except DagsterRunNotFoundError:
            # can happen if either this run or the root run in the run group was deleted
            return False
        if run_group is not None:
            _, run_group_iter = run_group
            # since the original run is in the run group, the number of retries launched
            # so far is len(run_group_iter) - 1
            if len(list(run_group_iter)) <= max_retries:
                return True
    return False
