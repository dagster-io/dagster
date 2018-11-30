from enum import Enum

from dagster import check

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


class EventRecord:
    def __init__(self, logger_message):
        self._logger_message = logger_message

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


class PipelineEventRecord(EventRecord):
    @property
    def pipeline_name(self):
        return self._logger_message.meta['pipeline']


class LogMessageRecord(EventRecord):
    pass


EVENT_CLS_LOOKUP = {
    EventType.PIPELINE_START: PipelineEventRecord,
    EventType.PIPELINE_SUCCESS: PipelineEventRecord,
    EventType.PIPELINE_FAILURE: PipelineEventRecord,
    EventType.UNCATEGORIZED: LogMessageRecord
}


def construct_event_record(logger_message):
    check.inst_param(logger_message, 'logger_message', StructuredLoggerMessage)
    event_type = construct_event_type(logger_message.meta.get('event_type'))
    log_record_cls = EVENT_CLS_LOOKUP[event_type]
    return log_record_cls(logger_message)


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
