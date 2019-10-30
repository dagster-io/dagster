from abc import ABCMeta, abstractmethod, abstractproperty

import six

from dagster import check

from .step import StepExecutionContext
from .system import SystemComputeExecutionContext


class AbstractComputeExecutionContext(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractmethod
    def has_tag(self, key):
        '''Implement this method to check if a logging tag is set.'''

    @abstractmethod
    def get_tag(self, key):
        '''Implement this method to get a logging tag.'''

    @abstractproperty
    def run_id(self):
        '''The run id for the context.'''

    @abstractproperty
    def solid_def(self):
        '''The solid definition corresponding to the execution step being executed.'''

    @abstractproperty
    def solid(self):
        '''The solid corresponding to the execution step being executed.'''

    @abstractproperty
    def pipeline_def(self):
        '''The pipeline being executed.'''

    @abstractproperty
    def resources(self):
        '''Resources available in the execution context.'''

    @abstractproperty
    def log(self):
        '''The log manager available in the execution context.'''


class ComputeExecutionContext(StepExecutionContext, AbstractComputeExecutionContext):
    __slots__ = ['_system_compute_execution_context']

    def __init__(self, system_compute_execution_context):
        self._system_compute_execution_context = check.inst_param(
            system_compute_execution_context,
            'system_compute_execution_context',
            SystemComputeExecutionContext,
        )
        super(ComputeExecutionContext, self).__init__(system_compute_execution_context)

    @property
    def solid_config(self):
        return self._system_compute_execution_context.solid_config

    @property
    def pipeline_run(self):
        return self._system_compute_execution_context.pipeline_run
