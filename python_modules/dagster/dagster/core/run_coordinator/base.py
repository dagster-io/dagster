from abc import ABC, abstractmethod
from typing import NamedTuple, Optional

from dagster.core.instance import MayHaveInstanceWeakref
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.workspace.context import IWorkspace, WorkspaceRequestContext


class SubmitRunContext(NamedTuple):
    """
    Context available within a run coordinator's submit_run method
    """

    pipeline_run: PipelineRun
    workspace: IWorkspace

    def get_request_header(self, key: str) -> Optional[str]:
        # if there is a source
        if isinstance(self.workspace, WorkspaceRequestContext) and self.workspace.source:
            headers = getattr(self.workspace.source, "headers", None)
            # and it has a headers property
            if headers:
                # do a get against it
                return headers.get(key)

        # otherwise return None
        return None


class RunCoordinator(ABC, MayHaveInstanceWeakref):
    @abstractmethod
    def submit_run(self, context: SubmitRunContext) -> PipelineRun:
        """
        Submit a run to the run coordinator for execution.

        Args:
            context (SubmitRunContext): information about the submission - every run coordinator
            will need the PipelineRun, and some run coordinators may need information from the
            IWorkspace from which the run was launched.

        Returns:
            PipelineRun: The queued run
        """

    @abstractmethod
    def cancel_run(self, run_id):
        """
        Cancels a run. The run may be queued in the coordinator, or it may have been launched.

        Returns False is the process was already canceled. Returns true if the cancellation was
        successful.
        """

    def dispose(self):
        """
        Do any resource cleanup that should happen when the DagsterInstance is
        cleaning itself up.
        """
