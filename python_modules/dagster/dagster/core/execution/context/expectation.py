from dagster import check

from .step import StepExecutionContext
from .system import SystemExpectationExecutionContext


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
