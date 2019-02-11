'''
This module defines the different notions of context passed to user code during pipeline
execution. There are currently four types of contexts defined:

1) PipelineExecutionContext
2) StepExecutionContext
3) TransformExecutionContext
4) ExpectationExecutionContext

They inherit from eac hother in reverse order. They are also relatively lightweight
objects, and a new one is created for every invocation into user space.

Additionally in order to maintain backwards compat (where info.context used to rule the day)
we have a separate class LegacyContextAdapter which can be easily deleted once we break
that API guarantee in 0.4.0.
'''

from abc import ABCMeta, abstractproperty, abstractmethod
from collections import namedtuple
import logging
import uuid
import warnings

import six


from dagster import check
from dagster.utils import merge_dicts
from dagster.utils.logging import INFO, define_colored_console_logger

from .definitions.expectation import ExpectationDefinition
from .definitions.input import InputDefinition
from .definitions.output import OutputDefinition
from .events import ExecutionEvents
from .types.marshal import PersistenceStrategy
from .log import DagsterLog


class ExecutionContext(namedtuple('_ExecutionContext', 'loggers resources tags')):
    '''
    The user-facing object in the context creation function. The user constructs
    this in order to effect the context creation process. This could be named
    PipelineExecutionContextCreationData although that seemed excessively verbose.
    '''

    def __new__(cls, loggers=None, resources=None, tags=None):
        return super(ExecutionContext, cls).__new__(
            cls,
            loggers=check.opt_list_param(loggers, 'loggers', logging.Logger),
            resources=resources,
            tags=check.opt_dict_param(tags, 'tags'),
        )

    @staticmethod
    def console_logging(log_level=INFO, resources=None):
        return ExecutionContext(
            loggers=[define_colored_console_logger('dagster', log_level)], resources=resources
        )


class ExecutionMetadata(namedtuple('_ExecutionMetadata', 'run_id tags event_callback loggers')):
    def __new__(cls, run_id=None, tags=None, event_callback=None, loggers=None):
        return super(ExecutionMetadata, cls).__new__(
            cls,
            run_id=check.str_param(run_id, 'run_id') if run_id else str(uuid.uuid4()),
            tags=check.opt_dict_param(tags, 'tags', key_type=str, value_type=str),
            event_callback=check.opt_callable_param(event_callback, 'event_callback'),
            loggers=check.opt_list_param(loggers, 'loggers'),
        )


DEFAULT_LOGGERS = [define_colored_console_logger('dagster')]


def _warn_about_context_property():
    warnings.warn(
        (
            'As of 3.0.2 the context property is deprecated. Before your code likely looked '
            'like info.context.some_method_or_property. All of the properties of the nested '
            'context object have been hoisted to the top level, so just rename your info '
            'object to context and access context.some_method_or_property. This property '
            'will be removed in 0.4.0.'
        )
    )


def _warn_about_config_property():
    warnings.warn(
        (
            'As of 3.0.2 the config property is deprecated. Use solid_config instead. '
            'This will be removed in 0.4.0.'
        )
    )


# Delete this after 0.4.0
class LegacyContextAdapter:
    '''
    This class mimics the object that was at info.context prior to 0.3.1. It exists in
    order to provide backwards compatibility.
    '''

    def __init__(self, pipeline_context):
        self._pipeline_context = check.inst_param(
            pipeline_context, 'pipeline_context', PipelineExecutionContext
        )

    def has_tag(self, key):
        check.str_param(key, 'key')
        return key in self._pipeline_context.tags

    def get_tag(self, key):
        check.str_param(key, 'key')
        return self._pipeline_context.tags[key]

    @property
    def run_id(self):
        return self._pipeline_context.run_id

    @property
    def event_callback(self):
        return self._pipeline_context.event_callback

    @property
    def has_event_callback(self):
        return self._pipeline_context.event_callback is not None

    @property
    def environment_config(self):
        return self._pipeline_context.environment_config

    @property
    def resources(self):
        return self._pipeline_context.resources

    @property
    def tags(self):
        return self._pipeline_context.tags

    @property
    def persistence_strategy(self):
        return self._pipeline_context.persistence_strategy

    @property
    def events(self):
        return self._pipeline_context.events

    @property
    def log(self):
        return self._pipeline_context.log

    @property
    def pipeline_def(self):
        return self._pipeline_context.pipeline_def

    def debug(self, msg, **kwargs):
        return self._pipeline_context.log.debug(msg, **kwargs)

    def info(self, msg, **kwargs):
        return self._pipeline_context.log.info(msg, **kwargs)

    def warning(self, msg, **kwargs):
        return self._pipeline_context.log.warning(msg, **kwargs)

    def error(self, msg, **kwargs):
        return self._pipeline_context.log.error(msg, **kwargs)

    def critical(self, msg, **kwargs):
        return self._pipeline_context.log.critical(msg, **kwargs)


class AbstractTransformExecutionContext(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractmethod
    def has_tag(self, key):
        pass

    @abstractmethod
    def get_tag(self, key):
        pass

    @abstractproperty
    def run_id(self):
        pass

    @abstractproperty
    def event_callback(self):
        pass

    @abstractmethod
    def has_event_callback(self):
        pass

    @abstractproperty
    def environment_config(self):
        pass

    @abstractproperty
    def context(self):
        pass

    @abstractproperty
    def step(self):
        pass

    @abstractproperty
    def solid_def(self):
        pass

    @abstractproperty
    def solid(self):
        pass

    @abstractproperty
    def pipeline_def(self):
        pass

    @abstractproperty
    def resources(self):
        pass

    @abstractproperty
    def log(self):
        pass


class PipelineExecutionContextData(
    namedtuple(
        '_PipelineExecutionContextData',
        'run_id resources environment_config persistence_strategy pipeline_def event_callback',
    )
):
    '''
    PipelineContextData is the data that remains context throughtout the entire execution
    of a pipeline.
    '''

    def __new__(
        cls,
        run_id,
        resources,
        environment_config,
        persistence_strategy,
        pipeline_def,
        event_callback=None,
    ):
        from .definitions.pipeline import PipelineDefinition

        return super(PipelineExecutionContextData, cls).__new__(
            cls,
            run_id=check.str_param(run_id, 'run_id'),
            resources=resources,
            environment_config=check.dict_param(environment_config, 'environment_config'),
            persistence_strategy=check.inst_param(
                persistence_strategy, 'persistence_strategy', PersistenceStrategy
            ),
            pipeline_def=check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            event_callback=check.opt_callable_param(event_callback, 'event_callback'),
        )


class PipelineExecutionContext(object):
    __slots__ = ['_pipeline_context_data', '_tags', '_log', '_legacy_context', '_events']

    def __init__(self, pipeline_context_data, tags, log):
        self._pipeline_context_data = check.inst_param(
            pipeline_context_data, 'pipeline_context_data', PipelineExecutionContextData
        )
        self._tags = check.dict_param(tags, 'tags')
        self._log = check.inst_param(log, 'log', DagsterLog) if log else DEFAULT_LOGGERS
        self._legacy_context = LegacyContextAdapter(self)
        self._events = ExecutionEvents(pipeline_context_data.pipeline_def.name, self._log)

    def for_step(self, step):
        from .execution_plan.objects import ExecutionStep

        check.inst_param(step, 'step', ExecutionStep)
        tags = merge_dicts(self.tags, step.tags)
        log = DagsterLog(self.run_id, tags, self.log.loggers)
        return StepExecutionContext(self._pipeline_context_data, tags, log, step)

    @property
    def resources(self):
        return self._pipeline_context_data.resources

    @property
    def run_id(self):
        return self._pipeline_context_data.run_id

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
    def context(self):
        _warn_about_context_property()
        return self._legacy_context


class StepExecutionContext(PipelineExecutionContext):
    __slots__ = ['_step']

    def __init__(self, pipeline_context_data, tags, log, step):
        from .execution_plan.objects import ExecutionStep

        self._step = check.inst_param(step, 'step', ExecutionStep)
        super(StepExecutionContext, self).__init__(pipeline_context_data, tags, log)

    def for_transform(self, solid_config):
        return TransformExecutionContext(
            self._pipeline_context_data, self.tags, self.log, self.step, solid_config
        )

    def for_expectation(self, inout_def, expectation_def):
        return ExpectationExecutionContext(
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


class TransformExecutionContext(StepExecutionContext, AbstractTransformExecutionContext):
    __slots__ = ['_solid_config']

    def __init__(self, pipeline_context_data, tags, log, step, solid_config):
        self._solid_config = solid_config
        super(TransformExecutionContext, self).__init__(pipeline_context_data, tags, log, step)

    @property
    def solid_config(self):
        return self._solid_config

    @property
    def config(self):
        _warn_about_config_property()
        return self._solid_config


class ExpectationExecutionContext(StepExecutionContext):
    __slots__ = ['_inout_def', '_expectation_def']

    def __init__(self, pipeline_context_data, tags, log, step, inout_def, expectation_def):
        self._expectation_def = check.inst_param(
            expectation_def, 'expectation_def', ExpectationDefinition
        )
        self._inout_def = check.inst_param(
            inout_def, 'inout_def', (InputDefinition, OutputDefinition)
        )
        super(ExpectationExecutionContext, self).__init__(pipeline_context_data, tags, log, step)

    @property
    def expectation_def(self):
        return self._expectation_def

    @property
    def inout_def(self):
        return self._inout_def
