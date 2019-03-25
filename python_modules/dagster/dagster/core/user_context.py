'''
This module defines the different notions of context passed to user code during pipeline
execution. There are currently four types of contexts defined:

1) StepExecutionContext
2) TransformExecutionContext
3) ExpectationExecutionContext

They inherit from each other in reverse order. They are also relatively lightweight
objects, and a new one is created for every invocation into user space.

Additionally in order to maintain backwards compatibility (where info.context used
to rule the day) we have a separate class LegacyContextAdapter which can be
easily deleted once we break that API guarantee in 0.4.0.
'''

from abc import ABCMeta, abstractproperty, abstractmethod
from collections import namedtuple
import logging
import warnings
import six
from dagster import check
from dagster.utils.logging import INFO, define_colored_console_logger
from .execution_context import (
    SystemPipelineExecutionContext,
    SystemExpectationExecutionContext,
    SystemStepExecutionContext,
    SystemTransformExecutionContext,
)


class ExecutionContext(namedtuple('_ExecutionContext', 'loggers resources tags')):
    '''
    The user-facing object in the context creation function. The user constructs
    this in order to effect the context creation process. This could be named
    SystemPipelineExecutionContextCreationData although that seemed excessively verbose.
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
class LegacyContextAdapter(object):
    __slots__ = ['_pipeline_context']
    '''
    This class mimics the object that was at info.context prior to 0.3.1. It exists in
    order to provide backwards compatibility.
    '''

    def __init__(self, pipeline_context):
        self._pipeline_context = check.inst_param(
            pipeline_context, 'pipeline_context', SystemPipelineExecutionContext
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


class StepExecutionContext(object):
    __slots__ = ['_system_step_execution_context', '_legacy_context']

    def __init__(self, system_step_execution_context):
        self._system_step_execution_context = check.inst_param(
            system_step_execution_context,
            'system_step_execution_context',
            SystemStepExecutionContext,
        )
        self._legacy_context = LegacyContextAdapter(system_step_execution_context)

    @property
    def resources(self):
        return self._system_step_execution_context.resources

    @property
    def run_id(self):
        return self._system_step_execution_context.run_id

    @property
    def environment_dict(self):
        return self._system_step_execution_context.environment_dict

    @property
    def pipeline_def(self):
        return self._system_step_execution_context.pipeline_def

    @property
    def log(self):
        return self._system_step_execution_context.log

    @property
    def context(self):
        _warn_about_context_property()
        return self._legacy_context
        # return self._system_step_execution_context.context

    @property
    def solid_def(self):
        return self._system_step_execution_context.solid_def

    @property
    def solid(self):
        return self._system_step_execution_context.solid

    def has_tag(self, key):
        return self._system_step_execution_context.has_tag(key)

    def get_tag(self, key):
        return self._system_step_execution_context.get_tag(key)

    def get_system_context(self):
        '''
        This allows advanced users (e.g. framework authors) to punch through
        to the underlying system context.
        '''
        return self._system_step_execution_context


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
    def context(self):
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


class TransformExecutionContext(StepExecutionContext, AbstractTransformExecutionContext):
    __slots__ = ['_system_transform_execution_context']

    def __init__(self, system_transform_execution_context):
        self._system_transform_execution_context = check.inst_param(
            system_transform_execution_context,
            'system_transform_execution_context',
            SystemTransformExecutionContext,
        )
        super(TransformExecutionContext, self).__init__(system_transform_execution_context)

    @property
    def solid_config(self):
        return self._system_transform_execution_context.solid_config

    @property
    def config(self):
        _warn_about_config_property()
        return self.solid_config


class ExpectationExecutionContext(StepExecutionContext):
    __slots__ = ['_system_expectation_execution_context']

    def __init__(self, system_expectation_execution_context):
        self._system_expectation_execution_context = check.inst_param(
            system_expectation_execution_context,
            'system_expectation_execution_context',
            SystemExpectationExecutionContext,
        )
        super(ExpectationExecutionContext, self).__init__(system_expectation_execution_context)

    @property
    def expectation_def(self):
        return self._system_expectation_execution_context.expectation_def

    @property
    def inout_def(self):
        return self._system_expectation_execution_context.inout_def
