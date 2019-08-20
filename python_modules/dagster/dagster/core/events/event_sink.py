import logging
from abc import ABCMeta

import six


class _EventSinkLogHandler(logging.Handler):
    def __init__(self, sink):
        self.sink = sink
        super(_EventSinkLogHandler, self).__init__()

    def emit(self, record):
        try:
            self.sink.handle_record(record)

        except Exception as e:  # pylint: disable=W0703
            logging.critical('Error during logging!')
            logging.exception(str(e))
            if self.sink.raise_on_error:
                raise


class EventSink(six.with_metaclass(ABCMeta)):
    '''
    EventSinks are used to to capture the events that are produced during a dagster run.
    '''

    def __init__(self, raise_on_error=False):
        self.raise_on_error = raise_on_error

    def on_pipeline_init(self):
        pass

    def on_pipeline_teardown(self):
        pass

    def on_raw_log_record(self, record):
        pass

    def on_dagster_event(self, dagster_event):
        pass

    def on_log_message(self, log_message):
        pass

    def get_logger(self):
        logger = logging.Logger('__event_sink')
        logger.addHandler(_EventSinkLogHandler(self))
        logger.setLevel(10)
        return logger

    def handle_record(self, record):
        from dagster.core.events.log import (
            construct_event_record,
            DagsterEventRecord,
            LogMessageRecord,
            StructuredLoggerMessage,
        )

        self.on_raw_log_record(record)

        event = construct_event_record(
            StructuredLoggerMessage(
                name=record.name,
                message=record.msg,
                level=record.levelno,
                meta=record.dagster_meta,
                record=record,
            )
        )
        if isinstance(event, LogMessageRecord):
            self.on_log_message(event)
        elif isinstance(event, DagsterEventRecord):
            self.on_dagster_event(event)


class InMemoryEventSink(EventSink):
    def __init__(self):
        super(InMemoryEventSink, self).__init__()
        self.dagster_event_records = []
        self.log_message_records = []

    def on_dagster_event(self, dagster_event):
        self.dagster_event_records.append(dagster_event)

    def on_log_message(self, log_message):
        self.log_message_records.append(log_message)


class CallbackEventSink(EventSink):
    def __init__(self, cb):
        super(CallbackEventSink, self).__init__()
        self.cb = cb

    def on_dagster_event(self, dagster_event):
        self.cb(dagster_event)

    def on_log_message(self, log_message):
        self.cb(log_message)
