from enum import Enum
from typing import NamedTuple, Optional


class DatabricksRunResultState(str, Enum):
    """
    See https://docs.databricks.com/dev-tools/api/2.0/jobs.html#runresultstate.
    """

    Success = "SUCCESS"
    Failed = "FAILED"
    TimedOut = "TIMEDOUT"
    Canceled = "CANCELED"


class DatabricksRunLifeCycleState(str, Enum):
    """
    See https://docs.databricks.com/dev-tools/api/2.0/jobs.html#jobsrunlifecyclestate.
    """

    Pending = "PENDING"
    Running = "RUNNING"
    Terminating = "TERMINATING"
    Terminated = "TERMINATED"
    Skipped = "SKIPPED"
    InternalError = "INTERNAL_ERROR"


DATABRICKS_RUN_TERMINATED_STATES = [
    DatabricksRunLifeCycleState.Terminating,
    DatabricksRunLifeCycleState.Terminated,
    DatabricksRunLifeCycleState.InternalError,
]


class DatabricksRunState(NamedTuple):
    """Represents the state of a Databricks job run."""

    life_cycle_state: "DatabricksRunLifeCycleState"
    result_state: Optional["DatabricksRunResultState"]
    state_message: str

    def has_terminated(self) -> bool:
        """Has the job terminated?"""
        return self.life_cycle_state in DATABRICKS_RUN_TERMINATED_STATES

    def is_successful(self) -> bool:
        """Was the job successful?"""
        return self.result_state == DatabricksRunResultState.Success
