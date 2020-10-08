"""Types returned by the Databricks API.
"""

from enum import Enum as PyEnum


class DatabricksRunResultState(PyEnum):
    """The result state of the run.

    If life_cycle_state = TERMINATED: if the run had a task, the result is guaranteed to be
        available, and it indicates the result of the task.
    If life_cycle_state = PENDING, RUNNING, or SKIPPED, the result state is not available.
    If life_cycle_state = TERMINATING or life_cycle_state = INTERNAL_ERROR: the result state
        is available if the run had a task and managed to start it.

    Once available, the result state never changes.

    See https://docs.databricks.com/dev-tools/api/latest/jobs.html#runresultstate.
    """

    Success = "SUCCESS"
    Failed = "FAILED"
    TimedOut = "TIMEDOUT"
    Canceled = "CANCELED"


class DatabricksRunLifeCycleState(PyEnum):
    """The life cycle state of a run.

    See https://docs.databricks.com/dev-tools/api/latest/jobs.html#runlifecyclestate.
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
