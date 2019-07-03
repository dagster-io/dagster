from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.core.definitions import ExpectationResult, Materialization, SolidHandle, TypeCheck
from dagster.core.log_manager import DagsterLogManager
from dagster.utils.error import SerializableErrorInfo


class DagsterEventType(Enum):
    STEP_OUTPUT = 'STEP_OUTPUT'
    STEP_INPUT = 'STEP_INPUT'
    STEP_FAILURE = 'STEP_FAILURE'
    STEP_START = 'STEP_START'
    STEP_SUCCESS = 'STEP_SUCCESS'
    STEP_SKIPPED = 'STEP_SKIPPED'
    STEP_MATERIALIZATION = 'STEP_MATERIALIZATION'
    STEP_EXPECTATION_RESULT = 'STEP_EXPECTATION_RESULT'

    PIPELINE_INIT_FAILURE = 'PIPELINE_INIT_FAILURE'

    PIPELINE_START = 'PIPELINE_START'
    PIPELINE_SUCCESS = 'PIPELINE_SUCCESS'
    PIPELINE_FAILURE = 'PIPELINE_FAILURE'

    PIPELINE_PROCESS_START = 'PIPELINE_PROCESS_START'
    PIPELINE_PROCESS_STARTED = 'PIPELINE_PROCESS_STARTED'


STEP_EVENTS = {
    DagsterEventType.STEP_INPUT,
    DagsterEventType.STEP_START,
    DagsterEventType.STEP_OUTPUT,
    DagsterEventType.STEP_FAILURE,
    DagsterEventType.STEP_SUCCESS,
    DagsterEventType.STEP_SKIPPED,
    DagsterEventType.STEP_MATERIALIZATION,
    DagsterEventType.STEP_EXPECTATION_RESULT,
}

FAILURE_EVENTS = {
    DagsterEventType.PIPELINE_INIT_FAILURE,
    DagsterEventType.PIPELINE_FAILURE,
    DagsterEventType.STEP_FAILURE,
}


def _assert_type(method, expected_type, actual_type):
    check.invariant(
        expected_type == actual_type,
        (
            '{method} only callable when event_type is {expected_type}, called on {actual_type}'
        ).format(method=method, expected_type=expected_type, actual_type=actual_type),
    )


def _validate_event_specific_data(event_type, event_specific_data):
    from dagster.core.execution.plan.objects import (
        StepOutputData,
        StepFailureData,
        StepSuccessData,
        StepInputData,
    )

    if event_type == DagsterEventType.STEP_OUTPUT:
        check.inst_param(event_specific_data, 'event_specific_data', StepOutputData)
    elif event_type == DagsterEventType.STEP_FAILURE:
        check.inst_param(event_specific_data, 'event_specific_data', StepFailureData)
    elif event_type == DagsterEventType.STEP_SUCCESS:
        check.inst_param(event_specific_data, 'event_specific_data', StepSuccessData)
    elif event_type == DagsterEventType.STEP_MATERIALIZATION:
        check.inst_param(event_specific_data, 'event_specific_data', StepMaterializationData)
    elif event_type == DagsterEventType.PIPELINE_PROCESS_STARTED:
        check.inst_param(event_specific_data, 'event_specific_data', PipelineProcessStartedData)
    elif event_type == DagsterEventType.STEP_INPUT:
        check.inst_param(event_specific_data, 'event_specific_data', StepInputData)

    return event_specific_data


class DagsterEvent(
    namedtuple(
        '_DagsterEvent',
        'event_type_value pipeline_name step_key solid_handle step_kind_value '
        'logging_tags event_specific_data',
    )
):
    @staticmethod
    def from_step(event_type, step_context, event_specific_data=None):
        from dagster.core.execution.context.system import SystemStepExecutionContext

        check.inst_param(step_context, 'step_context', SystemStepExecutionContext)

        event = DagsterEvent(
            check.inst_param(event_type, 'event_type', DagsterEventType).value,
            step_context.pipeline_def.name,
            step_context.step.key,
            step_context.step.solid_handle,
            step_context.step.kind.value,
            step_context.logging_tags,
            _validate_event_specific_data(event_type, event_specific_data),
        )

        log_fn = step_context.log.error if event_type in FAILURE_EVENTS else step_context.log.debug

        log_fn(
            '{event_type} for step {step_key}'.format(
                event_type=event_type, step_key=step_context.step.key
            ),
            dagster_event=event,
            pipeline_name=step_context.pipeline_def.name,
        )
        return event

    @staticmethod
    def from_pipeline(event_type, pipeline_context):
        from dagster.core.execution.context.system import SystemPipelineExecutionContext

        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
        pipeline_name = pipeline_context.pipeline_def.name

        event = DagsterEvent(
            check.inst_param(event_type, 'event_type', DagsterEventType).value,
            check.str_param(pipeline_name, 'pipeline_name'),
        )

        log_fn = (
            pipeline_context.log.error
            if event_type in FAILURE_EVENTS
            else pipeline_context.log.debug
        )

        log_fn(
            '{event_type} for pipeline {pipeline_name}'.format(
                event_type=event_type, pipeline_name=pipeline_name
            ),
            dagster_event=event,
            pipeline_name=pipeline_name,
        )
        return event

    def __new__(
        cls,
        event_type_value,
        pipeline_name,
        step_key=None,
        solid_handle=None,
        step_kind_value=None,
        logging_tags=None,
        event_specific_data=None,
    ):
        return super(DagsterEvent, cls).__new__(
            cls,
            check.str_param(event_type_value, 'event_type_value'),
            check.str_param(pipeline_name, 'pipeline_name'),
            check.opt_str_param(step_key, 'step_key'),
            check.opt_inst_param(solid_handle, 'solid_handle', SolidHandle),
            check.opt_str_param(step_kind_value, 'step_kind_value'),
            check.opt_dict_param(logging_tags, 'logging_tags'),
            _validate_event_specific_data(DagsterEventType(event_type_value), event_specific_data),
        )

    @property
    def solid_name(self):
        return self.solid_handle.name

    @property
    def solid_definition_name(self):
        return self.solid_handle.definition_name

    @property
    def event_type(self):
        return DagsterEventType(self.event_type_value)

    @property
    def is_step_event(self):
        return self.event_type in STEP_EVENTS

    @property
    def step_kind(self):
        from dagster.core.execution.plan.objects import StepKind

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
    def is_failure(self):
        return self.event_type in FAILURE_EVENTS

    @property
    def step_output_data(self):
        _assert_type('step_output_data', DagsterEventType.STEP_OUTPUT, self.event_type)
        return self.event_specific_data

    @property
    def step_success_data(self):
        _assert_type('step_success_data', DagsterEventType.STEP_SUCCESS, self.event_type)
        return self.event_specific_data

    @property
    def step_failure_data(self):
        _assert_type('step_failure_data', DagsterEventType.STEP_FAILURE, self.event_type)
        return self.event_specific_data

    @property
    def pipeline_process_started_data(self):
        _assert_type(
            'pipeline_process_started', DagsterEventType.PIPELINE_PROCESS_STARTED, self.event_type
        )
        return self.event_specific_data

    @property
    def step_materialization_data(self):
        _assert_type(
            'step_materialization_data', DagsterEventType.STEP_MATERIALIZATION, self.event_type
        )
        return self.event_specific_data

    @property
    def pipeline_init_failure_data(self):
        _assert_type(
            'pipeline_init_failure_data', DagsterEventType.PIPELINE_INIT_FAILURE, self.event_type
        )
        return self.event_specific_data

    @staticmethod
    def step_output_event(step_context, step_output_data):
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_OUTPUT,
            step_context=step_context,
            event_specific_data=step_output_data,
        )

    @staticmethod
    def step_failure_event(step_context, step_failure_data):
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_FAILURE,
            step_context=step_context,
            event_specific_data=step_failure_data,
        )

    @staticmethod
    def step_input_event(step_context, step_input_data):
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_INPUT,
            step_context=step_context,
            event_specific_data=step_input_data,
        )

    @staticmethod
    def step_start_event(step_context):
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_START, step_context=step_context
        )

    @staticmethod
    def step_success_event(step_context, success):
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_SUCCESS,
            step_context=step_context,
            event_specific_data=success,
        )

    @staticmethod
    def step_skipped_event(step_context):
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_SKIPPED, step_context=step_context
        )

    @staticmethod
    def step_materialization(step_context, materialization):
        check.inst_param(materialization, 'materialization', Materialization)
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_MATERIALIZATION,
            step_context=step_context,
            event_specific_data=StepMaterializationData(materialization),
        )

    @staticmethod
    def step_expectation_result(step_context, expectation_result):
        check.inst_param(expectation_result, 'expectation_result', ExpectationResult)
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_EXPECTATION_RESULT,
            step_context=step_context,
            event_specific_data=StepExpectationResultData(expectation_result),
        )

    @staticmethod
    def pipeline_start(pipeline_context):
        return DagsterEvent.from_pipeline(DagsterEventType.PIPELINE_START, pipeline_context)

    @staticmethod
    def pipeline_success(pipeline_context):
        return DagsterEvent.from_pipeline(DagsterEventType.PIPELINE_SUCCESS, pipeline_context)

    @staticmethod
    def pipeline_failure(pipeline_context):
        return DagsterEvent.from_pipeline(DagsterEventType.PIPELINE_FAILURE, pipeline_context)

    @staticmethod
    def pipeline_init_failure(pipeline_name, failure_data, log_manager):
        check.inst_param(failure_data, 'failure_data', PipelineInitFailureData)
        check.inst_param(log_manager, 'log_manager', DagsterLogManager)
        # this failure happens trying to bring up context so can't use from_pipeline

        event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_INIT_FAILURE.value,
            pipeline_name=pipeline_name,
            event_specific_data=failure_data,
        )
        log_manager.error(
            '{event_type} for pipeline {pipeline_name}'.format(
                event_type=DagsterEventType.PIPELINE_INIT_FAILURE, pipeline_name=pipeline_name
            ),
            dagster_event=event,
            pipeline_name=pipeline_name,
        )
        return event


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


class StepMaterializationData(namedtuple('_StepMaterializationData', 'materialization')):
    pass


class StepExpectationResultData(namedtuple('_StepExpectationResultData', 'expectation_result')):
    pass


class PipelineProcessStartedData(namedtuple('_PipelineProcessStartedData', 'process_id')):
    pass


class PipelineInitFailureData(namedtuple('_PipelineInitFailureData', 'error')):
    def __new__(cls, error):
        return super(PipelineInitFailureData, cls).__new__(
            cls, error=check.inst_param(error, 'error', SerializableErrorInfo)
        )
