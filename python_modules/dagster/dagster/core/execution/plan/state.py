from typing import Dict, NamedTuple

from dagster import check
from dagster.core.execution.retries import RetryState
from dagster.serdes import whitelist_for_serdes


@whitelist_for_serdes
class KnownExecutionState(
    NamedTuple(
        "_KnownExecutionState",
        [
            ("previous_retry_attempts", Dict[str, int]),
        ],
    )
):
    """
    A snapshot for the parts of an on going execution that need to be handed down when delegating
    step execution to another machine/process. This includes things like previous retries and
    resolved dynamic outputs.
    """

    def __new__(cls, previous_retry_attempts):

        return super(KnownExecutionState, cls).__new__(
            cls,
            check.dict_param(
                previous_retry_attempts, "previous_retry_attempts", key_type=str, value_type=int
            ),
        )

    def get_retry_state(self):
        return RetryState(self.previous_retry_attempts)
