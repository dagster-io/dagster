from abc import ABCMeta, abstractmethod

import six


class RunLauncher(six.with_metaclass(ABCMeta)):
    @abstractmethod
    def launch_run(self, instance, run):
        '''Launch a run on a remote instance.
        
        This method should create the run (instance.create_run) and kick off execution.
        It may emit engine events.
        
        Args:
            instance (DagsterInstance): The instance to use to launch the run.
            run (PipelineRun): The run to create and launch.
        '''
