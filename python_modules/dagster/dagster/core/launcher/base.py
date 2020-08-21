from abc import ABCMeta, abstractmethod

import six


class RunLauncher(six.with_metaclass(ABCMeta)):
    def initialize(self, instance):
        """
        Perform any initialization that depends on the surrounding DagsterInstance.

        Args:
            instance (DagsterInstance): The instance in which the run has been created.
        """

    @abstractmethod
    def launch_run(self, instance, run, external_pipeline):
        """Launch a run.

        This method should begin the execution of the specified run, and may emit engine events.
        Runs should be created in the instance (e.g., by calling
        ``DagsterInstance.create_run()``) *before* this method is called, and
        should be in the ``PipelineRunStatus.NOT_STARTED`` state. Typically, this method will
        not be invoked directly, but should be invoked through ``DagsterInstance.launch_run()``.

        Args:
            instance (DagsterInstance): The instance in which the run has been created.
            run (PipelineRun): The PipelineRun to launch.
            external_pipeline (ExternalPipeline): The pipeline that is being launched (currently
             optional during migration)

        Returns:
            PipelineRun: The launched run. This should be in the ``PipelineRunStatus.STARTED``
                state, or, if a synchronous failure occurs, the ``PipelineRunStatus.FAILURE`` state.
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

    def join(self):
        pass
