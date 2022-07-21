from abc import ABC, abstractmethod
from enum import Enum
from typing import NamedTuple, Optional

from dagster._core.instance import MayHaveInstanceWeakref
from dagster._core.origin import PipelinePythonOrigin
from dagster._core.storage.pipeline_run import PipelineRun
from dagster._core.workspace.workspace import IWorkspace
from dagster._serdes import whitelist_for_serdes


class LaunchRunContext(NamedTuple):
    """
    Context available within a run launcher's launch_run call.
    """

    pipeline_run: PipelineRun
    workspace: Optional[IWorkspace]

    @property
    def pipeline_code_origin(self) -> Optional[PipelinePythonOrigin]:
        return self.pipeline_run.pipeline_code_origin


class ResumeRunContext(NamedTuple):
    """
    Context available within a run launcher's resume_run call.
    """

    pipeline_run: PipelineRun
    workspace: Optional[IWorkspace]
    resume_attempt_number: Optional[int] = None

    @property
    def pipeline_code_origin(self) -> Optional[PipelinePythonOrigin]:
        return self.pipeline_run.pipeline_code_origin


@whitelist_for_serdes
class WorkerStatus(Enum):
    RUNNING = "RUNNING"
    NOT_FOUND = "NOT_FOUND"
    FAILED = "FAILED"
    SUCCESS = "SUCCESS"
    UNKNOWN = "UNKNOWN"


class CheckRunHealthResult(NamedTuple):
    """
    Result of a check_run_worker_health call.
    """

    status: WorkerStatus
    msg: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.status.value}: '{self.msg}'"


class RunLauncher(ABC, MayHaveInstanceWeakref):
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
    def terminate(self, run_id):
        """
        Terminates a process.

        Returns False is the process was already terminated. Returns true if
        the process was alive and was successfully terminated
        """

    def dispose(self):
        """
        Do any resource cleanup that should happen when the DagsterInstance is
        cleaning itself up.
        """

    def join(self, timeout=30):
        pass

    @property
    def supports_check_run_worker_health(self):
        """
        Whether the run launcher supports check_run_worker_health.
        """
        return False

    def check_run_worker_health(self, run: PipelineRun) -> CheckRunHealthResult:
        raise NotImplementedError(
            "This run launcher does not support run monitoring. Please disable it on your instance."
        )

    @property
    def supports_resume_run(self):
        """
        Whether the run launcher supports resume_run.
        """
        return False

    def resume_run(self, context: ResumeRunContext) -> None:
        raise NotImplementedError(
            "This run launcher does not support resuming runs. If using "
            "run monitoring, set max_resume_run_attempts to 0."
        )
