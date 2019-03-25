from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.core.execution_plan.objects import (
    StepKind,
    StepOutputData,
    StepFailureData,
    StepSuccessData,
)
from dagster.core.execution_context import SystemStepExecutionContext
from .logging import EventType


class ExecutionStepEventType(Enum):
    STEP_OUTPUT = 'STEP_OUTPUT'
    STEP_FAILURE = 'STEP_FAILURE'
    STEP_START = 'STEP_START'
    STEP_SUCCESS = 'STEP_SUCCESS'


class ExecutionStepEvent(
    namedtuple(
        '_ExecutionStepEvent',
        'event_type_value step_key solid_name solid_definition_name step_kind_value '
        'step_output_data step_failure_data step_success_data tags',
    )
):
    @staticmethod
    def from_step(event_type, step_context, step_output_data, step_failure_data, step_success_data):
        event = ExecutionStepEvent(
            check.inst_param(event_type, 'event_type', ExecutionStepEventType).value,
            step_context.step.key,
            step_context.step.solid.name,
            step_context.step.solid.definition.name,
            step_context.step.kind.value,
            step_output_data,
            step_failure_data,
            step_success_data,
            step_context.tags,
        )
        step_context.log.info(
            ('{event_type} for step {step_key}').format(
                event_type=event_type, step_key=step_context.step.key
            ),
            event_type=EventType.DAGSTER_EVENT.value,
            dagster_event=event,
            pipeline_name=step_context.pipeline_def.name,
        )
        return event

    def __new__(
        cls,
        event_type_value,
        step_key,
        solid_name,
        solid_definition_name,
        step_kind_value,
        step_output_data,
        step_failure_data,
        step_success_data,
        tags,
    ):
        return super(ExecutionStepEvent, cls).__new__(
            cls,
            check.str_param(event_type_value, 'event_type_value'),
            check.str_param(step_key, 'step_key'),
            check.str_param(solid_name, 'solid_name'),
            check.str_param(solid_definition_name, 'solid_definition_name'),
            check.str_param(step_kind_value, 'step_kind_value'),
            check.opt_inst_param(step_output_data, 'step_output_data', StepOutputData),
            check.opt_inst_param(step_failure_data, 'step_failure_data', StepFailureData),
            check.opt_inst_param(step_success_data, 'step_success_data', StepSuccessData),
            check.dict_param(tags, 'tags'),
        )

    @property
    def event_type(self):
        return ExecutionStepEventType(self.event_type_value)

    @property
    def step_kind(self):
        return StepKind(self.step_kind_value)

    @property
    def is_step_success(self):
        return not self.is_step_failure

    @property
    def is_successful_output(self):
        return self.event_type == ExecutionStepEventType.STEP_OUTPUT

    @property
    def is_step_failure(self):
        return self.event_type == ExecutionStepEventType.STEP_FAILURE

    @staticmethod
    def step_output_event(step_context, step_output_data):
        check.inst_param(step_context, 'step_context', SystemStepExecutionContext)

        return ExecutionStepEvent.from_step(
            event_type=ExecutionStepEventType.STEP_OUTPUT,
            step_context=step_context,
            step_output_data=check.inst_param(step_output_data, 'step_output_data', StepOutputData),
            step_failure_data=None,
            step_success_data=None,
        )

    @staticmethod
    def step_failure_event(step_context, step_failure_data):
        check.inst_param(step_context, 'step_context', SystemStepExecutionContext)

        return ExecutionStepEvent.from_step(
            event_type=ExecutionStepEventType.STEP_FAILURE,
            step_context=step_context,
            step_output_data=None,
            step_failure_data=check.inst_param(
                step_failure_data, 'step_failure_data', StepFailureData
            ),
            step_success_data=None,
        )

    @staticmethod
    def step_start_event(step_context):
        return ExecutionStepEvent.from_step(
            event_type=ExecutionStepEventType.STEP_START,
            step_context=step_context,
            step_output_data=None,
            step_failure_data=None,
            step_success_data=None,
        )

    @staticmethod
    def step_success_event(step_context, success):
        return ExecutionStepEvent.from_step(
            event_type=ExecutionStepEventType.STEP_SUCCESS,
            step_context=step_context,
            step_output_data=None,
            step_failure_data=None,
            step_success_data=success,
        )
