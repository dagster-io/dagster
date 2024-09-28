from enum import Enum
from typing import NamedTuple, Optional

from databricks.sdk.service import jobs


class DatabricksRunResultState(str, Enum):
    """See https://docs.databricks.com/dev-tools/api/2.0/jobs.html#runresultstate."""

    CANCELED = "CANCELED"
    FAILED = "FAILED"
    SUCCESS = "SUCCESS"
    TIMEDOUT = "TIMEDOUT"

    def is_successful(self) -> bool:
        return self == DatabricksRunResultState.SUCCESS


class DatabricksRunLifeCycleState(str, Enum):
    """See https://docs.databricks.com/dev-tools/api/2.0/jobs.html#jobsrunlifecyclestate."""

    BLOCKED = "BLOCKED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    QUEUED = "QUEUED"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SKIPPED = "SKIPPED"
    TERMINATED = "TERMINATED"
    TERMINATING = "TERMINATING"
    WAITING_FOR_RETRY = "WAITING_FOR_RETRY"

    def has_terminated(self) -> bool:
        return self in [
            DatabricksRunLifeCycleState.TERMINATING,
            DatabricksRunLifeCycleState.TERMINATED,
            DatabricksRunLifeCycleState.INTERNAL_ERROR,
            DatabricksRunLifeCycleState.SKIPPED,
        ]

    def is_skipped(self) -> bool:
        return self == DatabricksRunLifeCycleState.SKIPPED


class DatabricksRunState(NamedTuple):
    """Represents the state of a Databricks job run."""

    life_cycle_state: Optional["DatabricksRunLifeCycleState"]
    result_state: Optional["DatabricksRunResultState"]
    state_message: Optional[str]

    def has_terminated(self) -> bool:
        """Has the job terminated?"""
        return self.life_cycle_state is not None and self.life_cycle_state.has_terminated()

    def is_skipped(self) -> bool:
        return self.life_cycle_state is not None and self.life_cycle_state.is_skipped()

    def is_successful(self) -> bool:
        """Was the job successful?"""
        return self.result_state is not None and self.result_state.is_successful()

    @classmethod
    def from_databricks(cls, run_state: jobs.RunState) -> "DatabricksRunState":
        return cls(
            life_cycle_state=(
                DatabricksRunLifeCycleState(run_state.life_cycle_state.value)
                if run_state.life_cycle_state
                else None
            ),
            result_state=(
                DatabricksRunResultState(run_state.result_state.value)
                if run_state.result_state
                else None
            ),
            state_message=run_state.state_message,
        )
