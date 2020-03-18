import abc

import six


class Engine(six.with_metaclass(abc.ABCMeta)):  # pylint: disable=no-init
    '''
    The Engine abstraction exists to allow DAG execution to be broken up and distrubted in different ways.
    Each unique engine should map to some system for managing work, such as using multiple processes on a single machine or
    using a task queue service to distrbute work across remote machines.
    '''

    @staticmethod
    @abc.abstractmethod
    def execute(pipeline_context, execution_plan):
        '''
        For the given context and execution plan, orchestrate a series of sub plan executions in a way that satisfies the whole plan being executed.

        Args:
            pipeline_context (SystemPipelineExecutionContext): The pipeline execution context.
            execution_plan (ExecutionPlan): The plan to execute.
        '''
