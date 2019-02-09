from abc import ABCMeta, abstractproperty
from collections import namedtuple

import six

from dagster import check
from dagster.core.execution_context import RuntimeExecutionContext, DagsterLog

from .dependency import Solid
from .expectation import ExpectationDefinition
from .input import InputDefinition
from .output import OutputDefinition
from .pipeline import PipelineDefinition


class ContextCreationExecutionInfo(
    namedtuple('_ContextCreationExecutionInfo', 'config pipeline_def run_id')
):
    def __new__(cls, config, pipeline_def, run_id):
        return super(ContextCreationExecutionInfo, cls).__new__(
            cls,
            config,
            check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            check.str_param(run_id, 'run_id'),
        )


class ExpectationExecutionInfo(
    namedtuple('_ExpectationExecutionInfo', 'context inout_def solid expectation_def resources log')
):
    def __new__(cls, context, inout_def, solid, expectation_def):
        return super(ExpectationExecutionInfo, cls).__new__(
            cls,
            check.inst_param(context, 'context', RuntimeExecutionContext),
            check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition)),
            check.inst_param(solid, 'solid', Solid),
            check.inst_param(expectation_def, 'expectation_def', ExpectationDefinition),
            context.resources,
            DagsterLog(context),
        )


class ITransformExecutionInfo(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractproperty
    def context(self):
        pass

    @abstractproperty
    def config(self):
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
