from enum import Enum
from typing import NamedTuple, Optional


class DatabricksRunResultState(str, Enum):
    """See https://docs.databricks.com/dev-tools/api/2.0/jobs.html#runresultstate."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEDOUT = "TIMEDOUT"
    CANCELED = "CANCELED"

    def is_successful(self) -> bool:
        return self == DatabricksRunResultState.SUCCESS


class DatabricksRunLifeCycleState(str, Enum):
    """See https://docs.databricks.com/dev-tools/api/2.0/jobs.html#jobsrunlifecyclestate."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"
    SKIPPED = "SKIPPED"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    def has_terminated(self) -> bool:
        return self in [
            DatabricksRunLifeCycleState.TERMINATING,
            DatabricksRunLifeCycleState.TERMINATED,
            DatabricksRunLifeCycleState.INTERNAL_ERROR,
        ]


class DatabricksRunState(NamedTuple):
    """Represents the state of a Databricks job run."""

    life_cycle_state: "DatabricksRunLifeCycleState"
    result_state: Optional["DatabricksRunResultState"]
    state_message: str

    def has_terminated(self) -> bool:
        """Has the job terminated?"""
        return self.life_cycle_state.has_terminated()

    def is_successful(self) -> bool:
        """Was the job successful?"""
        return bool(self.result_state and self.result_state.is_successful())
