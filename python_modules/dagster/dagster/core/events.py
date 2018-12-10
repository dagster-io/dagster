from enum import Enum
import json

from dagster import check

from dagster.utils.error import (
    serializable_error_info_from_exc_info,
    SerializableErrorInfo,
)

from dagster.utils.logging import (
    DEBUG,
    StructuredLoggerHandler,
    StructuredLoggerMessage,
    construct_single_handler_logger,
)


class EventType(Enum):
    PIPELINE_START = 'PIPELINE_START'
    PIPELINE_SUCCESS = 'PIPELINE_SUCCESS'
    PIPELINE_FAILURE = 'PIPELINE_FAILURE'

    EXECUTION_PLAN_STEP_SUCCESS = 'EXECUTION_PLAN_STEP_SUCCESS'
    EXECUTION_PLAN_STEP_START = 'EXECUTION_PLAN_STEP_START'
    EXECUTION_PLAN_STEP_FAILURE = 'EXECUTION_PLAN_STEP_FAILURE'

    UNCATEGORIZED = 'UNCATEGORIZED'


class ExecutionEvents:
    def __init__(self, context):
        self.context = context

    def pipeline_start(self):
        self.check_pipeline_in_context()
        self.context.info(
            'Beginning execution of pipeline {pipeline}'.format(pipeline=self.pipeline_name()),
            event_type=EventType.PIPELINE_START.value,
        )

    def pipeline_success(self):
        self.check_pipeline_in_context()
        self.context.info(
            'Completing successful execution of pipeline {pipeline}'.format(
                pipeline=self.pipeline_name(),
            ),
            event_type=EventType.PIPELINE_SUCCESS.value,
        )

    def pipeline_failure(self):
        self.check_pipeline_in_context()
        self.context.info(
            'Completing failing execution of pipeline {pipeline}'.format(
                pipeline=self.pipeline_name()
            ),
            event_type=EventType.PIPELINE_FAILURE.value,
        )

    def execution_plan_step_start(self, step_key):
        check.str_param(step_key, 'step_key')
        self.context.info(
            'Beginning execution of {step_key}'.format(step_key=step_key),
            event_type=EventType.EXECUTION_PLAN_STEP_START.value,
            step_key=step_key,
        )

    def execution_plan_step_success(self, step_key, millis):
        check.str_param(step_key, 'step_key')
        check.float_param(millis, 'millis')

        self.context.info(
            'Execution of {step_key} succeeded in {millis}'.format(
                step_key=step_key,
                millis=millis,
            ),
            event_type=EventType.EXECUTION_PLAN_STEP_SUCCESS.value,
            millis=millis,
            step_key=step_key,
        )

    def execution_plan_step_failure(self, step_key, exc_info):
        check.str_param(step_key, 'step_key')
        self.context.info(
            'Execution of {step_key} failed'.format(step_key=step_key),
            event_type=EventType.EXECUTION_PLAN_STEP_FAILURE.value,
            step_key=step_key,
            # We really need a better serialization story here
            error_info=json.dumps(serializable_error_info_from_exc_info(exc_info)),
        )

    def pipeline_name(self):
        return self.context.get_context_value('pipeline')

    def check_pipeline_in_context(self):
        check.invariant(
            self.context.has_context_value('pipeline'),
            'Must have pipeline context value',
        )


EVENT_TYPE_VALUES = set([item.value for item in EventType])


def valid_event_type(event_type):
    check.opt_str_param(event_type, 'event_type')
    return event_type in EVENT_TYPE_VALUES


def construct_event_type(event_type):
    check.opt_str_param(event_type, 'event_type')
    return EventType(event_type) if valid_event_type(event_type) else EventType.UNCATEGORIZED


class EventRecord(object):
    def __init__(self, logger_message, error_info):
        self._logger_message = logger_message
        self._error_info = check.opt_inst_param(error_info, 'error_info', SerializableErrorInfo)

    @property
    def message(self):
        return self._logger_message.message

    @property
    def level(self):
        return self._logger_message.level

    @property
    def original_message(self):
        return self._logger_message.meta['orig_message']

    @property
    def event_type(self):
        event_type = self._logger_message.meta.get('event_type')
        return construct_event_type(event_type)

    @property
    def run_id(self):
        return self._logger_message.meta['run_id']

    @property
    def timestamp(self):
        return self._logger_message.record.created

    @property
    def error_info(self):
        return self._error_info


class PipelineEventRecord(EventRecord):
    @property
    def pipeline_name(self):
        return self._logger_message.meta['pipeline']


class ExecutionStepEventRecord(EventRecord):
    @property
    def step_key(self):
        return self._logger_message.meta['step_key']

    @property
    def pipeline_name(self):
        return self._logger_message.meta['pipeline']

    @property
    def solid_name(self):
        return self._logger_message.meta['solid']

    @property
    def solid_definition_name(self):
        return self._logger_message.meta['solid_definition']


class ExecutionStepSuccessRecord(ExecutionStepEventRecord):
    @property
    def millis(self):
        return self._logger_message.meta['millis']


class LogMessageRecord(EventRecord):
    pass


EVENT_CLS_LOOKUP = {
    EventType.EXECUTION_PLAN_STEP_FAILURE: ExecutionStepEventRecord,
    EventType.EXECUTION_PLAN_STEP_START: ExecutionStepEventRecord,
    EventType.EXECUTION_PLAN_STEP_SUCCESS: ExecutionStepSuccessRecord,
    EventType.PIPELINE_FAILURE: PipelineEventRecord,
    EventType.PIPELINE_START: PipelineEventRecord,
    EventType.PIPELINE_SUCCESS: PipelineEventRecord,
    EventType.UNCATEGORIZED: LogMessageRecord,
}


def construct_error_info(logger_message):
    if 'error_info' not in logger_message.meta:
        return None

    raw_error_info = logger_message.meta['error_info']

    message, stack = json.loads(raw_error_info)

    return SerializableErrorInfo(message, stack)


def construct_event_record(logger_message):
    check.inst_param(logger_message, 'logger_message', StructuredLoggerMessage)
    event_type = construct_event_type(logger_message.meta.get('event_type'))
    log_record_cls = EVENT_CLS_LOOKUP[event_type]

    return log_record_cls(logger_message, construct_error_info(logger_message))


def construct_event_logger(event_record_callback):
    '''
    Callback receives a stream of event_records
    '''
    check.callable_param(event_record_callback, 'event_record_callback')

    return construct_single_handler_logger(
        'event-logger',
        DEBUG,
        StructuredLoggerHandler(
            lambda logger_message: event_record_callback(construct_event_record(logger_message))
        ),
    )
