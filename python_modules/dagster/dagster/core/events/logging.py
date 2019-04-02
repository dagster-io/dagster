import json

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


class EventRecord(object):
    def __init__(
        self,
        error_info,
        message,
        level,
        user_message,
        run_id,
        timestamp,
        step_key=None,
        pipeline_name=None,
        dagster_event=None,
    ):
        from dagster.core.events import DagsterEvent

        self._error_info = check.opt_inst_param(error_info, 'error_info', SerializableErrorInfo)
        self._message = check.str_param(message, 'message')
        self._level = check_valid_level_param(level)
        self._user_message = check.str_param(user_message, 'user_message')
        self._run_id = check.str_param(run_id, 'run_id')
        self._timestamp = check.float_param(timestamp, 'timestamp')
        self._step_key = check.opt_str_param(step_key, 'step_key')
        self._pipeline_name = check.opt_str_param(pipeline_name, 'pipeline_name')
        self._dagster_event = check.opt_inst_param(dagster_event, 'dagster_event', DagsterEvent)

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
    def is_dagster_event(self):
        return bool(self._dagster_event)

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

    @property
    def pipeline_name(self):
        return self._pipeline_name

    @property
    def dagster_event(self):
        return self._dagster_event

    def to_dict(self):
        return {
            'run_id': self.run_id,
            'message': self.message,
            'level': self.level,
            'user_message': self.user_message,
            'timestamp': self.timestamp,
            'error_info': self.error_info,
            'step_key': self.step_key,
            'dagster_event': self.dagster_event,
            'pipeline_name': self.pipeline_name,
        }


class DagsterEventRecord(EventRecord):
    pass


class LogMessageRecord(EventRecord):
    pass


def construct_error_info(logger_message):
    if 'error_info' not in logger_message.meta:
        return None

    raw_error_info = logger_message.meta['error_info']

    message, stack = json.loads(raw_error_info)

    return SerializableErrorInfo(message, stack)


def construct_event_record(logger_message):
    check.inst_param(logger_message, 'logger_message', StructuredLoggerMessage)

    log_record_cls = LogMessageRecord
    if logger_message.meta.get('dagster_event'):
        log_record_cls = DagsterEventRecord

    return log_record_cls(
        message=logger_message.message,
        level=logger_message.level,
        user_message=logger_message.meta['orig_message'],
        run_id=logger_message.meta['run_id'],
        timestamp=logger_message.record.created,
        step_key=logger_message.meta.get('step_key'),
        pipeline_name=logger_message.meta.get('pipeline_name'),
        dagster_event=logger_message.meta.get('dagster_event'),
        error_info=construct_error_info(logger_message),
    )


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
