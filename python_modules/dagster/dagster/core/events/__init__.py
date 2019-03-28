from collections import namedtuple
from enum import Enum

from dagster import check

from .logging import EventType


class DagsterEventType(Enum):
    STEP_OUTPUT = 'STEP_OUTPUT'
    STEP_FAILURE = 'STEP_FAILURE'
    STEP_START = 'STEP_START'
    STEP_SUCCESS = 'STEP_SUCCESS'


def _validate_event_specific_data(event_type, event_specific_data):
    from dagster.core.execution_plan.objects import StepOutputData, StepFailureData, StepSuccessData

    if event_type == DagsterEventType.STEP_OUTPUT:
        check.inst_param(event_specific_data, 'event_specific_data', StepOutputData)
    elif event_type == DagsterEventType.STEP_FAILURE:
        check.inst_param(event_specific_data, 'event_specific_data', StepFailureData)
    elif event_type == DagsterEventType.STEP_SUCCESS:
        check.inst_param(event_specific_data, 'event_specific_data', StepSuccessData)

    return event_specific_data


class DagsterEvent(
    namedtuple(
        '_DagsterEvent',
        'event_type_value step_key pipeline_name solid_name solid_definition_name step_kind_value '
        'tags event_specific_data',
    )
):
    @staticmethod
    def from_step(event_type, step_context, event_specific_data=None):
        event = DagsterEvent(
            check.inst_param(event_type, 'event_type', DagsterEventType).value,
            step_context.step.key,
            step_context.pipeline_def.name,
            step_context.step.solid.name,
            step_context.step.solid.definition.name,
            step_context.step.kind.value,
            step_context.tags,
            event_specific_data,
        )

        log_fn = step_context.log.info
        if event_type == DagsterEventType.STEP_FAILURE:
            log_fn = step_context.log.error

        log_fn(
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
        pipeline_name,
        solid_name,
        solid_definition_name,
        step_kind_value,
        tags,
        event_specific_data,
    ):
        return super(DagsterEvent, cls).__new__(
            cls,
            check.str_param(event_type_value, 'event_type_value'),
            check.str_param(step_key, 'step_key'),
            check.str_param(pipeline_name, 'pipeline_name'),
            check.str_param(solid_name, 'solid_name'),
            check.str_param(solid_definition_name, 'solid_definition_name'),
            check.str_param(step_kind_value, 'step_kind_value'),
            check.dict_param(tags, 'tags'),
            _validate_event_specific_data(DagsterEventType(event_type_value), event_specific_data),
        )

    @property
    def event_type(self):
        return DagsterEventType(self.event_type_value)

    @property
    def step_kind(self):
        from dagster.core.execution_plan.objects import StepKind

        return StepKind(self.step_kind_value)

    @property
    def is_step_success(self):
        return not self.is_step_failure

    @property
    def is_successful_output(self):
        return self.event_type == DagsterEventType.STEP_OUTPUT

    @property
    def is_step_failure(self):
        return self.event_type == DagsterEventType.STEP_FAILURE

    @property
    def step_output_data(self):
        assert (
            self.event_type == DagsterEventType.STEP_OUTPUT
        ), 'step_output_data only available on STEP_OUTPUT'
        return self.event_specific_data

    @property
    def step_success_data(self):
        assert (
            self.event_type == DagsterEventType.STEP_SUCCESS
        ), 'step_success_data only available on STEP_SUCCESS'
        return self.event_specific_data

    @property
    def step_failure_data(self):
        assert (
            self.event_type == DagsterEventType.STEP_FAILURE
        ), 'step_failure_data only available on STEP_FAILURE'
        return self.event_specific_data

    @staticmethod
    def step_output_event(step_context, step_output_data):
        from dagster.core.execution_context import SystemStepExecutionContext

        check.inst_param(step_context, 'step_context', SystemStepExecutionContext)

        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_OUTPUT,
            step_context=step_context,
            event_specific_data=step_output_data,
        )

    @staticmethod
    def step_failure_event(step_context, step_failure_data):
        from dagster.core.execution_context import SystemStepExecutionContext

        check.inst_param(step_context, 'step_context', SystemStepExecutionContext)

        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_FAILURE,
            step_context=step_context,
            event_specific_data=step_failure_data,
        )

    @staticmethod
    def step_start_event(step_context):
        from dagster.core.execution_context import SystemStepExecutionContext

        check.inst_param(step_context, 'step_context', SystemStepExecutionContext)

        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_START, step_context=step_context
        )

    @staticmethod
    def step_success_event(step_context, success):
        from dagster.core.execution_context import SystemStepExecutionContext

        check.inst_param(step_context, 'step_context', SystemStepExecutionContext)

        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_SUCCESS,
            step_context=step_context,
            event_specific_data=success,
        )


def get_step_output_event(events, step_key, output_name='result'):
    check.list_param(events, 'events', of_type=DagsterEvent)
    check.str_param(step_key, 'step_key')
    check.str_param(output_name, 'output_name')
    for event in events:
        if (
            event.event_type == DagsterEventType.STEP_OUTPUT
            and event.step_key == step_key
            and event.step_output_data.output_name == output_name
        ):
            return event
    return None
