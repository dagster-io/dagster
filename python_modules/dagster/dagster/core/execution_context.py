'''
This module contains the execution context objects that are internal to the system.
Not every property on these should be exposed to random Jane or Joe dagster user
so we have a different layer of objects that encode the explicit public API
in the user_context module
'''
from collections import namedtuple
import uuid

from dagster import check
from dagster.utils import merge_dicts

from .definitions.expectation import ExpectationDefinition
from .definitions.input import InputDefinition
from .definitions.output import OutputDefinition
from .events import ExecutionEvents
from .log import DagsterLog
from .runs import RunStorageMode
from .system_config.objects import EnvironmentConfig
from .types.marshal import PersistenceStrategy


class ExecutorConfig:
    pass


class InProcessExecutorConfig(ExecutorConfig):
    def __init__(self, throw_on_user_error=True):
        self.throw_on_user_error = check.bool_param(throw_on_user_error, 'throw_on_user_error')


class MultiprocessExecutorConfig(ExecutorConfig):
    def __init__(self, pipeline_fn):
        self.pipeline_fn = check.callable_param(pipeline_fn, 'pipeline_fn')
        self.throw_on_user_error = False


def make_new_run_id():
    return str(uuid.uuid4())


class RunConfig(
    namedtuple('_RunConfig', ('run_id tags event_callback loggers executor_config storage_mode'))
):
    def __new__(
        cls,
        run_id=None,
        tags=None,
        event_callback=None,
        loggers=None,
        executor_config=None,
        storage_mode=None,
    ):

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
        )

    @staticmethod
    def nonthrowing_in_process():
        return RunConfig(executor_config=InProcessExecutorConfig(throw_on_user_error=False))

    def with_tags(self, **tags):
        return RunConfig(
            run_id=self.run_id,
            event_callback=self.event_callback,
            loggers=self.loggers,
            tags=merge_dicts(self.tags, tags),
            executor_config=self.executor_config,
            storage_mode=self.storage_mode,
        )


class SystemPipelineExecutionContextData(
    namedtuple(
        '_SystemPipelineExecutionContextData',
        (
            'run_config resources environment_config persistence_strategy pipeline_def '
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
        persistence_strategy,
        pipeline_def,
        run_storage,
        intermediates_manager,
    ):
        from .definitions.pipeline import PipelineDefinition

        return super(SystemPipelineExecutionContextData, cls).__new__(
            cls,
            run_config=check.inst_param(run_config, 'run_config', RunConfig),
            resources=resources,
            environment_config=check.inst_param(
                environment_config, 'environment_config', EnvironmentConfig
            ),
            persistence_strategy=check.inst_param(
                persistence_strategy, 'persistence_strategy', PersistenceStrategy
            ),
            pipeline_def=check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            # TODO typecheck
            run_storage=run_storage,
            intermediates_manager=intermediates_manager,
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
    __slots__ = ['_pipeline_context_data', '_tags', '_log', '_legacy_context', '_events']

    def __init__(self, pipeline_context_data, tags, log):
        self._pipeline_context_data = check.inst_param(
            pipeline_context_data, 'pipeline_context_data', SystemPipelineExecutionContextData
        )
        self._tags = check.dict_param(tags, 'tags')
        self._log = check.inst_param(log, 'log', DagsterLog)
        self._events = ExecutionEvents(pipeline_context_data.pipeline_def.name, self._log)

    def for_step(self, step):
        from .execution_plan.objects import ExecutionStep

        check.inst_param(step, 'step', ExecutionStep)

        tags = merge_dicts(self.tags, step.tags)
        log = DagsterLog(self.run_id, tags, self.log.loggers)
        return SystemStepExecutionContext(self._pipeline_context_data, tags, log, step)

    @property
    def executor_config(self):
        return self.run_config.executor_config

    @property
    def run_config(self):
        return self._pipeline_context_data.run_config

    @property
    def resources(self):
        return self._pipeline_context_data.resources

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
    def tags(self):
        return self._tags

    def has_tag(self, key):
        check.str_param(key, 'key')
        return key in self._tags

    def get_tag(self, key):
        check.str_param(key, 'key')
        return self._tags[key]

    @property
    def persistence_strategy(self):
        return self._pipeline_context_data.persistence_strategy

    @property
    def pipeline_def(self):
        return self._pipeline_context_data.pipeline_def

    @property
    def events(self):
        return self._events

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
            self._pipeline_context_data, self.tags, self.log, self.step
        )

    def for_expectation(self, inout_def, expectation_def):
        return SystemExpectationExecutionContext(
            self._pipeline_context_data, self.tags, self.log, self.step, inout_def, expectation_def
        )

    @property
    def step(self):
        return self._step

    @property
    def solid_def(self):
        return self._step.solid.definition

    @property
    def solid(self):
        return self._step.solid


class SystemTransformExecutionContext(SystemStepExecutionContext):
    @property
    def solid_config(self):
        solid_config = self.environment_config.solids.get(self.solid.name)
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
