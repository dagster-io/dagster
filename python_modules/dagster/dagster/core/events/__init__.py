'''Structured representations of system events.'''
from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.core.definitions import (
    EventMetadataEntry,
    ExpectationResult,
    Materialization,
    SolidHandle,
    TypeCheck,
)
from dagster.core.definitions.events import ObjectStoreOperationType
from dagster.core.execution.context.system import (
    SystemPipelineExecutionContext,
    SystemStepExecutionContext,
)
from dagster.core.execution.plan.objects import StepOutputData
from dagster.core.log_manager import DagsterLogManager
from dagster.core.serdes import whitelist_for_serdes
from dagster.utils.error import SerializableErrorInfo
from dagster.utils.timing import format_duration


class DagsterEventType(Enum):
    '''The types of events that may be yielded by solid and pipeline execution.'''

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
    PIPELINE_PROCESS_EXITED = 'PIPELINE_PROCESS_EXITED'

    OBJECT_STORE_OPERATION = 'OBJECT_STORE_OPERATION'

    ENGINE_EVENT = 'ENGINE_EVENT'


STEP_EVENTS = {
    DagsterEventType.STEP_INPUT,
    DagsterEventType.STEP_START,
    DagsterEventType.STEP_OUTPUT,
    DagsterEventType.STEP_FAILURE,
    DagsterEventType.STEP_SUCCESS,
    DagsterEventType.STEP_SKIPPED,
    DagsterEventType.STEP_MATERIALIZATION,
    DagsterEventType.STEP_EXPECTATION_RESULT,
    DagsterEventType.OBJECT_STORE_OPERATION,
}

FAILURE_EVENTS = {
    DagsterEventType.PIPELINE_INIT_FAILURE,
    DagsterEventType.PIPELINE_FAILURE,
    DagsterEventType.STEP_FAILURE,
}

PIPELINE_EVENTS = {
    DagsterEventType.PIPELINE_START,
    DagsterEventType.PIPELINE_SUCCESS,
    DagsterEventType.PIPELINE_FAILURE,
}


def _assert_type(method, expected_type, actual_type):
    check.invariant(
        expected_type == actual_type,
        (
            '{method} only callable when event_type is {expected_type}, called on {actual_type}'
        ).format(method=method, expected_type=expected_type, actual_type=actual_type),
    )


def _validate_event_specific_data(event_type, event_specific_data):
    from dagster.core.execution.plan.objects import StepFailureData, StepSuccessData, StepInputData

    if event_type == DagsterEventType.STEP_OUTPUT:
        check.inst_param(event_specific_data, 'event_specific_data', StepOutputData)
    elif event_type == DagsterEventType.STEP_FAILURE:
        check.inst_param(event_specific_data, 'event_specific_data', StepFailureData)
    elif event_type == DagsterEventType.STEP_SUCCESS:
        check.inst_param(event_specific_data, 'event_specific_data', StepSuccessData)
    elif event_type == DagsterEventType.STEP_MATERIALIZATION:
        check.inst_param(event_specific_data, 'event_specific_data', StepMaterializationData)
    elif event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
        check.inst_param(event_specific_data, 'event_specific_data', StepExpectationResultData)
    elif event_type == DagsterEventType.PIPELINE_PROCESS_STARTED:
        check.inst_param(event_specific_data, 'event_specific_data', PipelineProcessStartedData)
    elif event_type == DagsterEventType.PIPELINE_PROCESS_EXITED:
        check.inst_param(event_specific_data, 'event_specific_data', PipelineProcessExitedData)
    elif event_type == DagsterEventType.STEP_INPUT:
        check.inst_param(event_specific_data, 'event_specific_data', StepInputData)
    elif event_type == DagsterEventType.ENGINE_EVENT:
        check.inst_param(event_specific_data, 'event_specific_data', EngineEventData)

    return event_specific_data


def log_step_event(step_context, event):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.inst_param(event, 'event', DagsterEvent)

    event_type = DagsterEventType(event.event_type_value)
    log_fn = step_context.log.error if event_type in FAILURE_EVENTS else step_context.log.debug

    log_fn(
        event.message
        or '{event_type} for step {step_key}'.format(
            event_type=event_type, step_key=step_context.step.key
        ),
        dagster_event=event,
        pipeline_name=step_context.pipeline_def.name,
    )


def log_pipeline_event(pipeline_context, event):
    event_type = DagsterEventType(event.event_type_value)

    log_fn = (
        pipeline_context.log.error if event_type in FAILURE_EVENTS else pipeline_context.log.debug
    )

    log_fn(
        event.message
        or '{event_type} for pipeline {pipeline_name}'.format(
            event_type=event_type, pipeline_name=pipeline_context.pipeline_def.name
        ),
        dagster_event=event,
        pipeline_name=pipeline_context.pipeline_def.name,
    )


@whitelist_for_serdes
class DagsterEvent(
    namedtuple(
        '_DagsterEvent',
        'event_type_value pipeline_name step_key solid_handle step_kind_value '
        'logging_tags event_specific_data message',
    )
):
    '''Events yielded by solid and pipeline execution.

    Users should not instantiate this class.'''

    @staticmethod
    def from_step(event_type, step_context, event_specific_data=None, message=None):

        check.inst_param(step_context, 'step_context', SystemStepExecutionContext)

        event = DagsterEvent(
            check.inst_param(event_type, 'event_type', DagsterEventType).value,
            step_context.pipeline_def.name,
            step_context.step.key,
            step_context.step.solid_handle,
            step_context.step.kind.value,
            step_context.logging_tags,
            _validate_event_specific_data(event_type, event_specific_data),
            check.opt_str_param(message, 'message'),
        )

        log_step_event(step_context, event)

        return event

    @staticmethod
    def from_pipeline(event_type, pipeline_context, message=None, event_specific_data=None):
        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)

        pipeline_name = pipeline_context.pipeline_def.name

        event = DagsterEvent(
            check.inst_param(event_type, 'event_type', DagsterEventType).value,
            check.str_param(pipeline_name, 'pipeline_name'),
            message=check.opt_str_param(message, 'message'),
            event_specific_data=_validate_event_specific_data(event_type, event_specific_data),
        )

        log_pipeline_event(pipeline_context, event)

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
        message=None,
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
            check.opt_str_param(message, 'message'),
        )

    @property
    def solid_name(self):
        return self.solid_handle.name

    @property
    def solid_definition_name(self):
        return self.solid_handle.definition_name

    @property
    def event_type(self):
        '''DagsterEventType: The type of this event.'''
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
        return self.event_type == DagsterEventType.STEP_SUCCESS

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
    def is_pipeline_event(self):
        return self.event_type in PIPELINE_EVENTS

    @property
    def is_engine_event(self):
        return self.event_type == DagsterEventType.ENGINE_EVENT

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
    def pipeline_process_exited_data(self):
        _assert_type(
            'pipeline_process_exited', DagsterEventType.PIPELINE_PROCESS_EXITED, self.event_type
        )
        return self.event_specific_data

    @property
    def pipeline_process_start_data(self):
        _assert_type(
            'pipeline_process_start', DagsterEventType.PIPELINE_PROCESS_START, self.event_type
        )
        return self.event_specific_data

    @property
    def step_materialization_data(self):
        _assert_type(
            'step_materialization_data', DagsterEventType.STEP_MATERIALIZATION, self.event_type
        )
        return self.event_specific_data

    @property
    def step_expectation_result_data(self):
        _assert_type(
            'step_expectation_result_data',
            DagsterEventType.STEP_EXPECTATION_RESULT,
            self.event_type,
        )
        return self.event_specific_data

    @property
    def pipeline_init_failure_data(self):
        _assert_type(
            'pipeline_init_failure_data', DagsterEventType.PIPELINE_INIT_FAILURE, self.event_type
        )
        return self.event_specific_data

    @property
    def engine_event_data(self):
        _assert_type('engine_event_data', DagsterEventType.ENGINE_EVENT, self.event_type)
        return self.event_specific_data

    @staticmethod
    def step_output_event(step_context, step_output_data):
        check.inst_param(step_output_data, 'step_output_data', StepOutputData)
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_OUTPUT,
            step_context=step_context,
            event_specific_data=step_output_data,
            message='Yielded output "{output_name}" of type "{output_type}".{type_check_clause}'.format(
                output_name=step_output_data.step_output_handle.output_name,
                output_type=step_context.step.step_output_named(
                    step_output_data.step_output_handle.output_name
                ).runtime_type.name,
                type_check_clause=(
                    ' Warning! Type check failed.'
                    if not step_output_data.type_check_data.success
                    else ' (Type check passed).'
                )
                if step_output_data.type_check_data
                else ' (No type check).',
            ),
        )

    @staticmethod
    def step_failure_event(step_context, step_failure_data):
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_FAILURE,
            step_context=step_context,
            event_specific_data=step_failure_data,
            message='Execution of step "{step_key}" failed.'.format(step_key=step_context.step.key),
        )

    @staticmethod
    def step_input_event(step_context, step_input_data):
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_INPUT,
            step_context=step_context,
            event_specific_data=step_input_data,
            message='Got input "{input_name}" of type "{input_type}".{type_check_clause}'.format(
                input_name=step_input_data.input_name,
                input_type=step_context.step.step_input_named(
                    step_input_data.input_name
                ).runtime_type.name,
                type_check_clause=(
                    ' Warning! Type check failed.'
                    if not step_input_data.type_check_data.success
                    else ' (Type check passed).'
                )
                if step_input_data.type_check_data
                else ' (No type check).',
            ),
        )

    @staticmethod
    def step_start_event(step_context):
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_START,
            step_context=step_context,
            message='Started execution of step "{step_key}".'.format(
                step_key=step_context.step.key
            ),
        )

    @staticmethod
    def step_success_event(step_context, success):
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_SUCCESS,
            step_context=step_context,
            event_specific_data=success,
            message='Finished execution of step "{step_key}" in {duration}.'.format(
                # TODO: Make duration human readable
                # See: https://github.com/dagster-io/dagster/issues/1602
                step_key=step_context.step.key,
                duration=format_duration(success.duration_ms),
            ),
        )

    @staticmethod
    def step_skipped_event(step_context):
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_SKIPPED,
            step_context=step_context,
            message='Skipped execution of step "{step_key}".'.format(
                step_key=step_context.step.key
            ),
        )

    @staticmethod
    def step_materialization(step_context, materialization):
        check.inst_param(materialization, 'materialization', Materialization)
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_MATERIALIZATION,
            step_context=step_context,
            event_specific_data=StepMaterializationData(materialization),
            message=materialization.description
            if materialization.description
            else 'Materialized value{label_clause}.'.format(
                label_clause=' {label}'.format(label=materialization.label)
                if materialization.label
                else ''
            ),
        )

    @staticmethod
    def step_expectation_result(step_context, expectation_result):
        check.inst_param(expectation_result, 'expectation_result', ExpectationResult)

        def _msg():
            if expectation_result.description:
                return expectation_result.description

            return 'Expectation{label_clause} {result_verb}'.format(
                label_clause=' ' + expectation_result.label if expectation_result.label else '',
                result_verb='passed' if expectation_result.success else 'failed',
            )

        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_EXPECTATION_RESULT,
            step_context=step_context,
            event_specific_data=StepExpectationResultData(expectation_result),
            message=_msg(),
        )

    @staticmethod
    def pipeline_start(pipeline_context):
        return DagsterEvent.from_pipeline(
            DagsterEventType.PIPELINE_START,
            pipeline_context,
            message='Started execution of pipeline "{pipeline_name}".'.format(
                pipeline_name=pipeline_context.pipeline_def.name
            ),
        )

    @staticmethod
    def pipeline_success(pipeline_context):
        return DagsterEvent.from_pipeline(
            DagsterEventType.PIPELINE_SUCCESS,
            pipeline_context,
            message='Finished execution of pipeline "{pipeline_name}".'.format(
                pipeline_name=pipeline_context.pipeline_def.name
            ),
        )

    @staticmethod
    def pipeline_failure(pipeline_context):
        return DagsterEvent.from_pipeline(
            DagsterEventType.PIPELINE_FAILURE,
            pipeline_context,
            message='Execution of pipeline "{pipeline_name}" failed.'.format(
                pipeline_name=pipeline_context.pipeline_def.name
            ),
        )

    @staticmethod
    def pipeline_init_failure(pipeline_name, failure_data, log_manager):
        check.inst_param(failure_data, 'failure_data', PipelineInitFailureData)
        check.inst_param(log_manager, 'log_manager', DagsterLogManager)
        # this failure happens trying to bring up context so can't use from_pipeline

        event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_INIT_FAILURE.value,
            pipeline_name=pipeline_name,
            event_specific_data=failure_data,
            message=(
                'Pipeline failure during initialization of pipeline "{pipeline_name}. '
                'This may be due to a failure in initializing a resource or logger".'
            ).format(pipeline_name=pipeline_name),
        )
        log_manager.error(
            event.message
            or '{event_type} for pipeline {pipeline_name}'.format(
                event_type=DagsterEventType.PIPELINE_INIT_FAILURE, pipeline_name=pipeline_name
            ),
            dagster_event=event,
            pipeline_name=pipeline_name,
        )
        return event

    @staticmethod
    def engine_event(pipeline_context, message, event_specific_data=None):
        return DagsterEvent.from_pipeline(
            DagsterEventType.ENGINE_EVENT,
            pipeline_context,
            message,
            event_specific_data=event_specific_data,
        )

    @staticmethod
    def object_store_operation(step_context, object_store_operation_result):
        object_store_name = (
            '{object_store_name} '.format(
                object_store_name=object_store_operation_result.object_store_name
            )
            if object_store_operation_result.object_store_name
            else ''
        )

        serialization_strategy_modifier = (
            ' using {serialization_strategy_name}'.format(
                serialization_strategy_name=object_store_operation_result.serialization_strategy_name
            )
            if object_store_operation_result.serialization_strategy_name
            else ''
        )

        value_name = object_store_operation_result.value_name

        if (
            ObjectStoreOperationType(object_store_operation_result.op)
            == ObjectStoreOperationType.SET_OBJECT
        ):
            message = (
                'Stored intermediate object for output {value_name} in '
                '{object_store_name}object store{serialization_strategy_modifier}.'
            ).format(
                value_name=value_name,
                object_store_name=object_store_name,
                serialization_strategy_modifier=serialization_strategy_modifier,
            )
        elif (
            ObjectStoreOperationType(object_store_operation_result.op)
            == ObjectStoreOperationType.GET_OBJECT
        ):
            message = (
                'Retrieved intermediate object for input {value_name} in '
                '{object_store_name}object store{serialization_strategy_modifier}.'
            ).format(
                value_name=value_name,
                object_store_name=object_store_name,
                serialization_strategy_modifier=serialization_strategy_modifier,
            )
        elif (
            ObjectStoreOperationType(object_store_operation_result.op)
            == ObjectStoreOperationType.CP_OBJECT
        ):
            message = (
                'Copied intermediate object for input {value_name} from {key} to {dest_key}'
            ).format(
                value_name=value_name,
                key=object_store_operation_result.key,
                dest_key=object_store_operation_result.dest_key,
            )
        else:
            message = ''

        return DagsterEvent.from_step(
            DagsterEventType.OBJECT_STORE_OPERATION,
            step_context,
            event_specific_data=ObjectStoreOperationResultData(
                op=object_store_operation_result.op,
                value_name=value_name,
                metadata_entries=[
                    EventMetadataEntry.path(object_store_operation_result.key, label='key')
                ],
            ),
            message=message,
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


@whitelist_for_serdes
class StepMaterializationData(namedtuple('_StepMaterializationData', 'materialization')):
    pass


@whitelist_for_serdes
class StepExpectationResultData(namedtuple('_StepExpectationResultData', 'expectation_result')):
    pass


@whitelist_for_serdes
class ObjectStoreOperationResultData(
    namedtuple('_ObjectStoreOperationResultData', 'op value_name metadata_entries')
):
    pass


@whitelist_for_serdes
class EngineEventData(namedtuple('_EngineEventData', 'metadata_entries error')):
    # serdes log
    # * added optional error
    #
    def __new__(cls, metadata_entries, error=None):
        return super(EngineEventData, cls).__new__(
            cls,
            metadata_entries=check.list_param(
                metadata_entries, 'metadata_entries', EventMetadataEntry
            ),
            error=check.opt_inst_param(error, 'error', SerializableErrorInfo),
        )

    @staticmethod
    def in_process(pid, step_keys_to_execute=None):
        check.int_param(pid, 'pid')
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute')
        return EngineEventData(
            metadata_entries=[EventMetadataEntry.text(str(pid), 'pid')]
            + (
                [EventMetadataEntry.text(str(step_keys_to_execute), 'step_keys')]
                if step_keys_to_execute
                else []
            )
        )

    @staticmethod
    def multiprocess(pid, parent_pid=None, step_keys_to_execute=None):
        check.int_param(pid, 'pid')
        check.opt_int_param(parent_pid, 'parent_pid')
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute')
        return EngineEventData(
            metadata_entries=[EventMetadataEntry.text(str(pid), 'pid')]
            + ([EventMetadataEntry.text(str(parent_pid), 'parent_pid')] if parent_pid else [])
            + (
                [EventMetadataEntry.text(str(step_keys_to_execute), 'step_keys')]
                if step_keys_to_execute
                else []
            )
        )

    @staticmethod
    def interrupted(steps_interrupted):
        check.list_param(steps_interrupted, 'steps_interrupted', str)
        return EngineEventData(
            metadata_entries=[EventMetadataEntry.text(str(steps_interrupted), 'steps_interrupted')]
        )

    @staticmethod
    def engine_error(error):
        check.inst_param(error, 'error', SerializableErrorInfo)
        return EngineEventData(metadata_entries=[], error=error)


@whitelist_for_serdes
class PipelineProcessStartedData(
    namedtuple('_PipelineProcessStartedData', 'process_id pipeline_name run_id')
):
    pass


@whitelist_for_serdes
class PipelineProcessExitedData(
    namedtuple('_PipelineProcessExitedData', 'process_id pipeline_name run_id')
):
    pass


@whitelist_for_serdes
class PipelineProcessStartData(namedtuple('_PipelineProcessStartData', 'pipeline_name run_id')):
    pass


@whitelist_for_serdes
class PipelineInitFailureData(namedtuple('_PipelineInitFailureData', 'error')):
    def __new__(cls, error):
        return super(PipelineInitFailureData, cls).__new__(
            cls, error=check.inst_param(error, 'error', SerializableErrorInfo)
        )
