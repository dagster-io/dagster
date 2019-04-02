import json

from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.utils.error import SerializableErrorInfo

from dagster.utils.logging import (
    DEBUG,
    StructuredLoggerHandler,
    JsonEventLoggerHandler,
    StructuredLoggerMessage,
    check_valid_level_param,
    construct_single_handler_logger,
)

from dagster.core.log import DagsterLog


class EventType(Enum):
    DAGSTER_EVENT = 'DAGSTER_EVENT'

    PIPELINE_PROCESS_START = 'PIPELINE_PROCESS_START'
    PIPELINE_PROCESS_STARTED = 'PIPELINE_PROCESS_STARTED'

    UNCATEGORIZED = 'UNCATEGORIZED'


class ExecutionEvents(namedtuple('_ExecutionEvents', 'pipeline_name log')):
    def __new__(cls, pipeline_name, log):
        return super(ExecutionEvents, cls).__new__(
            cls,
            check.str_param(pipeline_name, 'pipeline_name'),
            check.inst_param(log, 'log', DagsterLog),
        )


EVENT_TYPE_VALUES = {item.value for item in EventType}


def valid_event_type(event_type):
    check.opt_str_param(event_type, 'event_type')
    return event_type in EVENT_TYPE_VALUES


def construct_event_type(event_type):
    check.opt_str_param(event_type, 'event_type')
    return EventType(event_type) if valid_event_type(event_type) else EventType.UNCATEGORIZED


class EventRecord(object):
    def __init__(
        self, error_info, message, level, user_message, event_type, run_id, timestamp, step_key=None
    ):
        self._error_info = check.opt_inst_param(error_info, 'error_info', SerializableErrorInfo)
        self._message = check.str_param(message, 'message')
        self._level = check_valid_level_param(level)
        self._user_message = check.str_param(user_message, 'user_message')
        self._event_type = check.inst_param(event_type, 'event_type', EventType)
        self._run_id = check.str_param(run_id, 'run_id')
        self._timestamp = check.float_param(timestamp, 'timestamp')
        self._step_key = check.opt_str_param(step_key, 'step_key')

    @property
    def message(self):
        return self._message

    @property
    def level(self):
        return self._level

    @property
    def user_message(self):
        return self._user_message

    @property
    def event_type(self):
        return self._event_type

    @property
    def run_id(self):
        return self._run_id

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def error_info(self):
        return self._error_info

    @property
    def step_key(self):
        return self._step_key

    def to_dict(self):
        return {
            'run_id': self.run_id,
            'message': self.message,
            'level': self.level,
            'user_message': self.user_message,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp,
            'error_info': self._error_info,
            'step_key': self._step_key,
        }


class PipelineEventRecord(EventRecord):
    def __init__(self, pipeline_name, **kwargs):
        super(PipelineEventRecord, self).__init__(**kwargs)
        self._pipeline_name = check.str_param(pipeline_name, 'pipeline_name')

    @property
    def pipeline_name(self):
        return self._pipeline_name

    def to_dict(self):
        orig = super(PipelineEventRecord, self).to_dict()
        orig['pipeline_name'] = self.pipeline_name
        return orig


class DagsterEventRecord(EventRecord):
    def __init__(self, dagster_event, pipeline_name, **kwargs):
        super(DagsterEventRecord, self).__init__(**kwargs)
        self._dagster_event = dagster_event
        self._pipeline_name = pipeline_name

    @property
    def dagster_event(self):
        return self._dagster_event

    @property
    def pipeline_name(self):
        return self._pipeline_name

    def to_dict(self):
        orig = super(DagsterEventRecord, self).to_dict()
        orig.update({'dagster_event': self.dagster_event, 'pipeline_name': self.pipeline_name})
        return orig


class LogMessageRecord(EventRecord):
    pass


EVENT_CLS_LOOKUP = {
    EventType.DAGSTER_EVENT: DagsterEventRecord,
    EventType.UNCATEGORIZED: LogMessageRecord,
}


def construct_error_info(logger_message):
    if 'error_info' not in logger_message.meta:
        return None

    raw_error_info = logger_message.meta['error_info']

    message, stack = json.loads(raw_error_info)

    return SerializableErrorInfo(message, stack)


def is_pipeline_event_type(event_type):
    event_cls = EVENT_CLS_LOOKUP[event_type]
    return issubclass(event_cls, PipelineEventRecord)


def logger_to_kwargs(logger_message):
    event_type = construct_event_type(logger_message.meta.get('event_type'))

    base_args = {
        'message': logger_message.message,
        'level': logger_message.level,
        'user_message': logger_message.meta['orig_message'],
        'event_type': event_type,
        'run_id': logger_message.meta['run_id'],
        'timestamp': logger_message.record.created,
        'step_key': logger_message.meta.get('step_key'),
    }

    event_cls = EVENT_CLS_LOOKUP[event_type]
    if issubclass(event_cls, DagsterEventRecord):
        return dict(
            base_args,
            dagster_event=logger_message.meta['dagster_event'],
            pipeline_name=logger_message.meta['pipeline_name'],
        )
    else:
        return base_args


def construct_event_record(logger_message):
    check.inst_param(logger_message, 'logger_message', StructuredLoggerMessage)
    event_type = construct_event_type(logger_message.meta.get('event_type'))
    log_record_cls = EVENT_CLS_LOOKUP[event_type]

    kwargs = logger_to_kwargs(logger_message)
    return log_record_cls(error_info=construct_error_info(logger_message), **kwargs)


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


def construct_json_event_logger(json_path):
    '''Record a stream of event records to json'''
    check.str_param(json_path, 'json_path')
    return construct_single_handler_logger(
        "json-event-record-logger",
        DEBUG,
        JsonEventLoggerHandler(
            json_path,
            lambda record: construct_event_record(
                StructuredLoggerMessage(
                    name=record.name,
                    message=record.msg,
                    level=record.levelno,
                    meta=record.dagster_meta,
                    record=record,
                )
            ),
        ),
    )
