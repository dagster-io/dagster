from abc import ABCMeta, abstractmethod
from collections import namedtuple

import six

from dagster import check
from dagster.core.definitions.handle import ExecutionTargetHandle
from dagster.core.execution.config import ExecutorConfig
from dagster.core.storage.pipeline_run import PipelineRun


class StepRunRef(
    namedtuple(
        '_StepRunRef',
        'environment_dict pipeline_run run_id executor_config step_key execution_target_handle '
        'prior_attempts_count',
    )
):
    '''
    A serializable object that specifies what's needed to hydrate a step so that it can
    be executed in a process outside the plan process.
    '''

    def __new__(
        cls,
        environment_dict,
        pipeline_run,
        run_id,
        executor_config,
        step_key,
        execution_target_handle,
        prior_attempts_count,
    ):
        return super(StepRunRef, cls).__new__(
            cls,
            check.dict_param(environment_dict, 'environment_dict', key_type=str),
            check.inst_param(pipeline_run, 'pipeline_run', PipelineRun),
            check.str_param(run_id, 'run_id'),
            check.inst_param(executor_config, 'executor_config', ExecutorConfig),
            check.str_param(step_key, 'step_key'),
            check.inst_param(
                execution_target_handle, 'execution_target_handle', ExecutionTargetHandle
            ),
            check.int_param(prior_attempts_count, 'prior_attempts_count'),
        )


class StepLauncher(six.with_metaclass(ABCMeta)):
    '''
    A StepLauncher is responsible for executing steps, either in-process or in an external process.
    '''

    @abstractmethod
    def launch_step(self, step_context, prior_attempts_count):
        '''
        Args:
            step_context (SystemStepExecutionContext): The context that we're executing the step in.
            int: The number of times this step has been attempted in the same run.

        Returns:
            Iterator[DagsterEvent]: The events for the step.
        '''
