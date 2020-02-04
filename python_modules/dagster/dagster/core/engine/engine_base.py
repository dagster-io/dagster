import abc

import six


class Engine(six.with_metaclass(abc.ABCMeta)):  # pylint: disable=no-init
    @staticmethod
    @abc.abstractmethod
    def execute(pipeline_context, execution_plan):
        '''Core execution method.

        Args:
            pipeline_context (SystemPipelineExecutionContext): The pipeline execution context.
            execution_plan (ExecutionPlan): The plan to execute.
        '''
