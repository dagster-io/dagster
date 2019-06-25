from collections import namedtuple
import json

from dagster import check
from dagster.core.events import DagsterEvent
from dagster.core.log_manager import coerce_valid_log_level
from dagster.utils.error import SerializableErrorInfo
from dagster.utils.log import (
    StructuredLoggerHandler,
    JsonEventLoggerHandler,
    StructuredLoggerMessage,
    construct_single_handler_logger,
)


class EventRecord(
    namedtuple(
        '_EventRecord',
        'error_info message level user_message run_id timestamp step_key pipeline_name dagster_event',
    )
):
    def __new__(
        cls,
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
        return super(EventRecord, cls).__new__(
            cls,
            check.opt_inst_param(error_info, 'error_info', SerializableErrorInfo),
            check.str_param(message, 'message'),
            coerce_valid_log_level(level),
            check.str_param(user_message, 'user_message'),
            check.str_param(run_id, 'run_id'),
            check.float_param(timestamp, 'timestamp'),
            check.opt_str_param(step_key, 'step_key'),
            check.opt_str_param(pipeline_name, 'pipeline_name'),
            check.opt_inst_param(dagster_event, 'dagster_event', DagsterEvent),
        )

    @property
    def is_dagster_event(self):
        return bool(self.dagster_event)


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
    Callback receives a stream of event_records. Piggybacks on the logging machinery.
    '''
    check.callable_param(event_record_callback, 'event_record_callback')

    return construct_single_handler_logger(
        'event-logger',
        'debug',
        StructuredLoggerHandler(
            lambda logger_message: event_record_callback(construct_event_record(logger_message))
        ),
    )


def construct_json_event_logger(json_path):
    '''Record a stream of event records to json'''
    check.str_param(json_path, 'json_path')
    return construct_single_handler_logger(
        "json-event-record-logger",
        'debug',
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
