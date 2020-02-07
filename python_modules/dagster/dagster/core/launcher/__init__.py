from abc import ABCMeta, abstractmethod

import six


class RunLauncher(six.with_metaclass(ABCMeta)):
    @abstractmethod
    def launch_run(self, instance, run):
        '''Launch a run on a remote instance.
        
        This method should create the run (e.g., by calling ``instance.create_run``)
        and kick off its execution. This method may emit engine events.
        
        Args:
            instance (DagsterInstance): The instance to use to launch the run.
            run (PipelineRun): The run to create and launch.

        Returns:
            PipelineRun: The newly created run.
        '''
