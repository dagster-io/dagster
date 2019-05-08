'''
This module defines the different notions of context passed to user code during pipeline
execution. There are currently four types of contexts defined:

1) StepExecutionContext
2) TransformExecutionContext
3) ExpectationExecutionContext

They inherit from each other in reverse order. They are also relatively lightweight
objects, and a new one is created for every invocation into user space.
'''

from abc import ABCMeta, abstractproperty, abstractmethod
from collections import namedtuple
import logging
import six
from dagster import check
from dagster.utils.logging import INFO, define_colored_console_logger

from .execution_context import (
    SystemExpectationExecutionContext,
    SystemStepExecutionContext,
    SystemTransformExecutionContext,
)


class ExecutionContext(namedtuple('_ExecutionContext', 'loggers resources tags')):
    '''
    The user-facing object in the context creation function. The user constructs
    this in order to effect the context creation process. This could be named
    SystemPipelineExecutionContextCreationData although that seemed excessively verbose.

    Args:
        loggers (List[Logger]):
        resources ():
        tags (dict[str, str])
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


class StepExecutionContext(object):
    __slots__ = ['_system_step_execution_context', '_legacy_context']

    def __init__(self, system_step_execution_context):
        self._system_step_execution_context = check.inst_param(
            system_step_execution_context,
            'system_step_execution_context',
            SystemStepExecutionContext,
        )

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
    def solid_handle(self):
        return self._system_step_execution_context.solid_handle

    @property
    def solid(self):
        return self._system_step_execution_context.pipeline_def.get_solid(self.solid_handle)

    @property
    def solid_def(self):
        return self._system_step_execution_context.pipeline_def.get_solid(
            self.solid_handle
        ).definition

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
