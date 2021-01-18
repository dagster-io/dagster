from abc import ABC, abstractmethod

from dagster.core.instance import MayHaveInstanceWeakref


class RunLauncher(ABC, MayHaveInstanceWeakref):
    @abstractmethod
    def launch_run(self, run, external_pipeline):
        """Launch a run.

        This method should begin the execution of the specified run, and may emit engine events.
        Runs should be created in the instance (e.g., by calling
        ``DagsterInstance.create_run()``) *before* this method is called, and
        should be in the ``PipelineRunStatus.NOT_STARTED`` state. Typically, this method will
        not be invoked directly, but should be invoked through ``DagsterInstance.launch_run()``.

        Args:
            run (PipelineRun): The PipelineRun to launch.
            external_pipeline (ExternalPipeline): The pipeline that is being launched (currently
             optional during migration)

        Returns:
            PipelineRun: The launched run.
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
