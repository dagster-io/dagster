from collections import defaultdict
from enum import Enum
from typing import Mapping, Optional

from dagster import (
    Field,
    Selector,
    _check as check,
)
from dagster._serdes.serdes import whitelist_for_serdes


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
        for selector, _ in config_value.items():
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
