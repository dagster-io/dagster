'''
This module contains the execution context objects that are internal to the system.
Not every property on these should be exposed to random Jane or Joe dagster user
so we have a different layer of objects that encode the explicit public API
in the user_context module
'''
from collections import namedtuple
import uuid
import multiprocessing

from dagster import check
from dagster.utils import merge_dicts
from dagster.core.errors import DagsterInvariantViolationError

from .definitions.expectation import ExpectationDefinition
from .definitions.input import InputDefinition
from .definitions.output import OutputDefinition
from .log import DagsterLog
from .runs import RunStorageMode, RunStorage
from .system_config.objects import EnvironmentConfig


class ExecutorConfig:
    pass


class InProcessExecutorConfig(ExecutorConfig):
    def __init__(self, raise_on_error=True):
        self.raise_on_error = check.bool_param(raise_on_error, 'raise_on_error')


class MultiprocessExecutorConfig(ExecutorConfig):
    def __init__(self, pipeline_fn, max_concurrent=None):
        self.pipeline_fn = check.callable_param(pipeline_fn, 'pipeline_fn')
        max_concurrent = (
            max_concurrent if max_concurrent is not None else multiprocessing.cpu_count()
        )
        self.max_concurrent = check.int_param(max_concurrent, 'max_concurrent')
        check.invariant(self.max_concurrent > 0, 'max_concurrent processes must be greater than 0')
        self.raise_on_error = False


def make_new_run_id():
    return str(uuid.uuid4())


class ReexecutionConfig:
    def __init__(self, previous_run_id, step_output_handles):
        self.previous_run_id = previous_run_id
        self.step_output_handles = step_output_handles


class RunConfig(
    namedtuple(
        '_RunConfig',
        (
            'run_id tags event_callback loggers executor_config storage_mode reexecution_config '
            'step_keys_to_execute'
        ),
    )
):
    '''
    Configuration that controls the details of how Dagster will execute a pipeline.

    Args:
      run_id (str): The ID to use for this run. If not provided a new UUID will be created using `uuid4`.
      tags (dict[str, str]): Key value pairs that will be added to logs.
      event_callback (callable): A callback to invoke with each :py:class:`EventRecord` produced during execution.
      loggers (list): Additional loggers that log messages will be sent to.
      executor_config (ExecutorConfig): Configuration for where and how computation will occur.
      storage_mode (RunStorageMode): Where intermediate artifacts will be stored during execution.
      rexecution_config (RexecutionConfig): Information about a previous run to allow for subset rexecution.
      step_keys_to_execute (list[str]): They subset of steps from a pipeline to execute this run.
    '''

    def __new__(
        cls,
        run_id=None,
        tags=None,
        event_callback=None,
        loggers=None,
        executor_config=None,
        storage_mode=None,
        reexecution_config=None,
        step_keys_to_execute=None,
    ):
        if (
            isinstance(executor_config, MultiprocessExecutorConfig)
            and storage_mode is RunStorageMode.IN_MEMORY
        ):
            raise DagsterInvariantViolationError(
                'Can not create a RunConfig with executor_config MultiProcessExecutorConfig and '
                'storage_mode RunStorageMode.IN_MEMORY'
            )

        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

        return super(RunConfig, cls).__new__(
            cls,
            run_id=check.str_param(run_id, 'run_id') if run_id else make_new_run_id(),
            tags=check.opt_dict_param(tags, 'tags', key_type=str, value_type=str),
            event_callback=check.opt_callable_param(event_callback, 'event_callback'),
            loggers=check.opt_list_param(loggers, 'loggers'),
            executor_config=check.inst_param(executor_config, 'executor_config', ExecutorConfig)
            if executor_config
            else InProcessExecutorConfig(),
            storage_mode=check.opt_inst_param(storage_mode, 'storage_mode', RunStorageMode),
            reexecution_config=check.opt_inst_param(
                reexecution_config, 'reexecution_config', ReexecutionConfig
            ),
            step_keys_to_execute=step_keys_to_execute,
        )

    @staticmethod
    def nonthrowing_in_process():
        return RunConfig(executor_config=InProcessExecutorConfig(raise_on_error=False))

    def with_tags(self, **new_tags):
        new_tags = merge_dicts(self.tags, new_tags)
        return RunConfig(**merge_dicts(self._asdict(), {'tags': new_tags}))


class SystemPipelineExecutionContextData(
    namedtuple(
        '_SystemPipelineExecutionContextData',
        (
            'run_config resources environment_config pipeline_def '
            'run_storage intermediates_manager'
        ),
    )
):
    '''
    PipelineContextData is the data that remains context throughtout the entire execution
    of a pipeline.
    '''

    def __new__(
        cls,
        run_config,
        resources,
        environment_config,
        pipeline_def,
        run_storage,
        intermediates_manager,
    ):
        from .definitions import PipelineDefinition
        from .intermediates_manager import IntermediatesManager

        return super(SystemPipelineExecutionContextData, cls).__new__(
            cls,
            run_config=check.inst_param(run_config, 'run_config', RunConfig),
            resources=resources,
            environment_config=check.inst_param(
                environment_config, 'environment_config', EnvironmentConfig
            ),
            pipeline_def=check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            run_storage=check.inst_param(run_storage, 'run_storage', RunStorage),
            intermediates_manager=check.inst_param(
                intermediates_manager, 'intermediates_manager', IntermediatesManager
            ),
        )

    @property
    def run_id(self):
        return self.run_config.run_id

    @property
    def event_callback(self):
        return self.run_config.event_callback

    @property
    def environment_dict(self):
        return self.environment_config.original_config_dict


class SystemPipelineExecutionContext(object):
    __slots__ = ['_pipeline_context_data', '_logging_tags', '_log', '_legacy_context', '_events']

    def __init__(self, pipeline_context_data, logging_tags, log):
        self._pipeline_context_data = check.inst_param(
            pipeline_context_data, 'pipeline_context_data', SystemPipelineExecutionContextData
        )
        self._logging_tags = check.dict_param(logging_tags, 'logging_tags')
        self._log = check.inst_param(log, 'log', DagsterLog)

    def for_step(self, step):
        from .execution_plan.objects import ExecutionStep

        check.inst_param(step, 'step', ExecutionStep)

        logging_tags = merge_dicts(self.logging_tags, step.logging_tags)
        log = DagsterLog(self.run_id, logging_tags, self.log.loggers)
        return SystemStepExecutionContext(self._pipeline_context_data, logging_tags, log, step)

    @property
    def executor_config(self):
        return self.run_config.executor_config

    @property
    def run_config(self):
        return self._pipeline_context_data.run_config

    @property
    def resources(self):
        return self._pipeline_context_data.resources.build()

    @property
    def run_id(self):
        return self._pipeline_context_data.run_id

    @property
    def environment_dict(self):
        return self._pipeline_context_data.environment_dict

    @property
    def environment_config(self):
        return self._pipeline_context_data.environment_config

    @property
    def logging_tags(self):
        return self._logging_tags

    def has_tag(self, key):
        check.str_param(key, 'key')
        return key in self._logging_tags

    def get_tag(self, key):
        check.str_param(key, 'key')
        return self._logging_tags[key]

    @property
    def pipeline_def(self):
        return self._pipeline_context_data.pipeline_def

    @property
    def event_callback(self):
        return self._pipeline_context_data.event_callback

    def has_event_callback(self):
        return self._pipeline_context_data.event_callback is not None

    @property
    def log(self):
        return self._log

    @property
    def run_storage(self):
        return self._pipeline_context_data.run_storage

    @property
    def intermediates_manager(self):
        return self._pipeline_context_data.intermediates_manager


class SystemStepExecutionContext(SystemPipelineExecutionContext):
    __slots__ = ['_step']

    def __init__(self, pipeline_context_data, tags, log, step):
        from .execution_plan.objects import ExecutionStep

        self._step = check.inst_param(step, 'step', ExecutionStep)
        super(SystemStepExecutionContext, self).__init__(pipeline_context_data, tags, log)

    def for_transform(self):
        return SystemTransformExecutionContext(
            self._pipeline_context_data, self.logging_tags, self.log, self.step
        )

    def for_expectation(self, inout_def, expectation_def):
        return SystemExpectationExecutionContext(
            self._pipeline_context_data,
            self.logging_tags,
            self.log,
            self.step,
            inout_def,
            expectation_def,
        )

    @property
    def step(self):
        return self._step

    @property
    def solid_handle(self):
        return self._step.solid_handle

    @property
    def solid_def(self):
        return self.solid.definition

    @property
    def solid(self):
        return self.pipeline_def.get_solid(self._step.solid_handle)

    @property
    def resources(self):
        return self._pipeline_context_data.resources.build(
            self.solid.resource_mapper_fn, self.solid_def.resources
        )


class SystemTransformExecutionContext(SystemStepExecutionContext):
    @property
    def solid_config(self):
        solid_config = self.environment_config.solids.get(str(self.solid_handle))
        return solid_config.config if solid_config else None


class SystemExpectationExecutionContext(SystemStepExecutionContext):
    __slots__ = ['_inout_def', '_expectation_def']

    def __init__(self, pipeline_context_data, tags, log, step, inout_def, expectation_def):
        self._expectation_def = check.inst_param(
            expectation_def, 'expectation_def', ExpectationDefinition
        )
        self._inout_def = check.inst_param(
            inout_def, 'inout_def', (InputDefinition, OutputDefinition)
        )
        super(SystemExpectationExecutionContext, self).__init__(
            pipeline_context_data, tags, log, step
        )

    @property
    def expectation_def(self):
        return self._expectation_def

    @property
    def inout_def(self):
        return self._inout_def
