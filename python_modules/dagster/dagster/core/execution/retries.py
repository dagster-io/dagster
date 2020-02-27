from collections import defaultdict
from enum import Enum

from dagster import Field, Permissive, Selector, check


def get_retries_config():
    return Field(
        Selector({'enabled': {}, 'disabled': {}, 'deferred': {'previous_attempts': Permissive()}}),
        is_required=False,
        default_value={'enabled': {}},
    )


class RetryMode(Enum):
    ENABLED = 'enabled'
    DISABLED = 'disabled'
    # Designed for use of in_process engine within "orchestrator" engine such as multiprocess,
    # up_for_retry steps are not directly re-enqued, deferring that to the outer engine.
    DEFERRED = 'deferred'


class Retries:
    def __init__(self, mode, previous_attempts=None):
        self._mode = check.inst_param(mode, 'mode', RetryMode)
        self._attempts = defaultdict(int)
        for key, val in check.opt_dict_param(
            previous_attempts, 'previous_attempts', key_type=str, value_type=int
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

    @staticmethod
    def from_config(config_value):
        for selector, value in config_value.items():
            return Retries(RetryMode(selector), value.get('previous_attempts'))
