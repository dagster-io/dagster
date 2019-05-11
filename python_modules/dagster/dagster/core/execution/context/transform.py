from abc import ABCMeta, abstractproperty, abstractmethod

import six

from dagster import check

from .step import StepExecutionContext
from .system import SystemTransformExecutionContext


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
