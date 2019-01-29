from collections import namedtuple

from dagster import check
from dagster.core.execution_context import RuntimeExecutionContext

from .dependency import Solid
from .expectation import ExpectationDefinition
from .input import InputDefinition
from .output import OutputDefinition
from .pipeline import PipelineDefinition


class DagsterLog:
    def __init__(self, context):
        self.context = context

    def debug(self, msg, **kwargs):
        return self.context.debug(msg, **kwargs)

    def info(self, msg, **kwargs):
        return self.context.info(msg, **kwargs)

    def warning(self, msg, **kwargs):
        return self.context.warning(msg, **kwargs)

    def error(self, msg, **kwargs):
        return self.context.error(msg, **kwargs)

    def critical(self, msg, **kwargs):
        return self.context.critical(msg, **kwargs)


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


class TransformExecutionInfo(
    namedtuple('_TransformExecutionInfo', 'context config solid pipeline_def resources log')
):
    '''An instance of TransformExecutionInfo is passed every solid transform function.

    Attributes:

        context (ExecutionContext): Context instance for this pipeline invocation
        config (Any): Config object for current solid
    '''

    def __new__(cls, context, config, solid, pipeline_def):
        return super(TransformExecutionInfo, cls).__new__(
            cls,
            check.inst_param(context, 'context', RuntimeExecutionContext),
            config,
            check.inst_param(solid, 'solid', Solid),
            check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            context.resources,
            DagsterLog(context),
        )

    @property
    def solid_def(self):
        return self.solid.definition
