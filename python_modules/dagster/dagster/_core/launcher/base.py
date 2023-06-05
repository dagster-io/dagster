from abc import ABC, abstractmethod
from enum import Enum
from typing import NamedTuple, Optional

from dagster._core.instance import MayHaveInstanceWeakref, T_DagsterInstance
from dagster._core.origin import JobPythonOrigin
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.workspace.workspace import IWorkspace
from dagster._serdes import whitelist_for_serdes


class LaunchRunContext(NamedTuple):
    """Context available within a run launcher's launch_run call."""

    dagster_run: DagsterRun
    workspace: Optional[IWorkspace]

    @property
    def job_code_origin(self) -> Optional[JobPythonOrigin]:
        return self.dagster_run.job_code_origin


class ResumeRunContext(NamedTuple):
    """Context available within a run launcher's resume_run call."""

    dagster_run: DagsterRun
    workspace: Optional[IWorkspace]
    resume_attempt_number: Optional[int] = None

    @property
    def job_code_origin(self) -> Optional[JobPythonOrigin]:
        return self.dagster_run.job_code_origin


@whitelist_for_serdes
class WorkerStatus(Enum):
    RUNNING = "RUNNING"
    NOT_FOUND = "NOT_FOUND"
    FAILED = "FAILED"
    SUCCESS = "SUCCESS"
    UNKNOWN = "UNKNOWN"


class CheckRunHealthResult(NamedTuple):
    """Result of a check_run_worker_health call."""

    status: WorkerStatus
    msg: Optional[str] = None
    transient: Optional[bool] = None
    run_worker_id: Optional[str] = None  # Identifier for a particular run worker

    def __str__(self) -> str:
        return f"{self.status.value}: '{self.msg}'"


class RunLauncher(ABC, MayHaveInstanceWeakref[T_DagsterInstance]):
    @abstractmethod
    def launch_run(self, context: LaunchRunContext) -> None:
        """Launch a run.

        This method should begin the execution of the specified run, and may emit engine events.
        Runs should be created in the instance (e.g., by calling
        ``DagsterInstance.create_run()``) *before* this method is called, and
        should be in the ``PipelineRunStatus.STARTING`` state. Typically, this method will
        not be invoked directly, but should be invoked through ``DagsterInstance.launch_run()``.

        Args:
            context (LaunchRunContext): information about the launch - every run launcher
            will need the PipelineRun, and some run launchers may need information from the
            IWorkspace from which the run was launched.
        """

    @abstractmethod
    def terminate(self, run_id: str) -> bool:
        """Terminates a process.

        Returns False is the process was already terminated. Returns true if
        the process was alive and was successfully terminated
        """

    def dispose(self) -> None:
        """Do any resource cleanup that should happen when the DagsterInstance is
        cleaning itself up.
        """

    def join(self, timeout: int = 30) -> None:
        pass

    @property
    def supports_check_run_worker_health(self) -> bool:
        """Whether the run launcher supports check_run_worker_health."""
        return False

    def check_run_worker_health(self, run: DagsterRun) -> CheckRunHealthResult:
        raise NotImplementedError(
            "This run launcher does not support run monitoring. Please disable it on your instance."
        )

    def get_run_worker_debug_info(self, run: DagsterRun) -> Optional[str]:
        return None

    @property
    def supports_resume_run(self) -> bool:
        """Whether the run launcher supports resume_run."""
        return False

    def resume_run(self, context: ResumeRunContext) -> None:
        raise NotImplementedError(
            "This run launcher does not support resuming runs. If using "
            "run monitoring, set max_resume_run_attempts to 0."
        )
