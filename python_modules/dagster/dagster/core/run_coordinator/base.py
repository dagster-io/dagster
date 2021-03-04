from abc import ABC, abstractmethod

from dagster.core.instance import MayHaveInstanceWeakref


class RunCoordinator(ABC, MayHaveInstanceWeakref):
    @abstractmethod
    def submit_run(self, pipeline_run, external_pipeline):
        """
        Submit a run to the run coordinator for execution.

        Args:
            pipeline_run (PipelineRun): The run
            external_pipeline (ExternalPipeline): The pipeline

        Returns:
            PipelineRun: The queued run
        """

    @abstractmethod
    def can_cancel_run(self, run_id):
        """
        Can this run_id be canceled
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
