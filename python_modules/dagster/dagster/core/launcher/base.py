from abc import ABC, abstractmethod
from typing import NamedTuple, Optional

from dagster.core.instance import MayHaveInstanceWeakref
from dagster.core.origin import PipelinePythonOrigin
from dagster.core.storage.dagster_run import DagsterRun
from dagster.core.workspace.workspace import IWorkspace


class LaunchRunContext(NamedTuple):
    """
    Context available within a run launcher's launch_run call.
    """

    dagster_run: DagsterRun
    workspace: Optional[IWorkspace]

    @property
    def pipeline_code_origin(self) -> Optional[PipelinePythonOrigin]:
        return self.dagster_run.pipeline_code_origin


class RunLauncher(ABC, MayHaveInstanceWeakref):
    @abstractmethod
    def launch_run(self, context: LaunchRunContext) -> None:
        """Launch a run.

        This method should begin the execution of the specified run, and may emit engine events.
        Runs should be created in the instance (e.g., by calling
        ``DagsterInstance.create_run()``) *before* this method is called, and
        should be in the ``DagsterRunStatus.STARTING`` state. Typically, this method will
        not be invoked directly, but should be invoked through ``DagsterInstance.launch_run()``.

        Args:
            context (LaunchRunContext): information about the launch - every run launcher
            will need the DagsterRun, and some run launchers may need information from the
            IWorkspace from which the run was launched.
        """

    @abstractmethod
    def can_terminate(self, run_id):
        """
        Can this run_id be terminated by this run launcher.
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
