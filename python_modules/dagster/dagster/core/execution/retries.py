from collections import defaultdict
from enum import Enum

from dagster import Field, Selector, check


def get_retries_config():
    return Field(
        Selector({"enabled": {}, "disabled": {}}),
        is_required=False,
        default_value={"enabled": {}},
    )


class RetryMode(Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    # Designed for use of inner plan execution within "orchestrator" engine such as multiprocess,
    # up_for_retry steps are not directly re-enqueued, deferring that to the engine.
    DEFERRED = "deferred"


class Retries:
    def __init__(self, mode, previous_attempts=None):
        self._mode = check.inst_param(mode, "mode", RetryMode)
        self._attempts = defaultdict(int)
        for key, val in check.opt_dict_param(
            previous_attempts, "previous_attempts", key_type=str, value_type=int
        ).items():
            self._attempts[key] = val

    @property
    def enabled(self):
        return self._mode == RetryMode.ENABLED

    @property
    def disabled(self):
        return self._mode == RetryMode.DISABLED

    @property
    def deferred(self):
        return self._mode == RetryMode.DEFERRED

    def get_attempt_count(self, key):
        return self._attempts[key]

    def mark_attempt(self, key):
        self._attempts[key] += 1

    def for_inner_plan(self):
        if self.disabled or self.deferred:
            return self
        elif self.enabled:
            return Retries(mode=RetryMode.DEFERRED, previous_attempts=dict(self._attempts))
        else:
            check.failed("Unexpected Retries state! Expected enabled, disabled, or deferred")

    @staticmethod
    def from_config(config_value):
        for selector, value in config_value.items():
            return Retries(RetryMode(selector), value.get("previous_attempts"))

    def to_config(self):
        value = {self._mode.value: {}}
        if self.deferred:
            value[self._mode.value] = {"previous_attempts": dict(self._attempts)}
        return value

    @staticmethod
    def disabled_mode():
        return Retries(RetryMode.DISABLED)

    def to_graphql_input(self):
        previous_attempts_list = []
        for k, v in self._attempts.items():
            previous_attempts_list.append({"key": k, "count": v})

        return {
            "mode": self._mode.value,
            "retriesPreviousAttempts": previous_attempts_list,
        }

    @staticmethod
    def from_graphql_input(graphql_data):
        if graphql_data == None:
            return graphql_data
        previous_attempts = {}
        for item in graphql_data.retries_previous_attempts:
            previous_attempts[item.get("key")] = item.get("count")
        return Retries(mode=RetryMode(graphql_data.mode), previous_attempts=previous_attempts)
