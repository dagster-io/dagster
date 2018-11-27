from dagster.utils.logging import (
    define_structured_logger,
    DEBUG,
)

from dagster import ExecutionContext
from dagster.core.events import EventType


def test_structured_logger_in_context():
    messages = []

    def _append_message(logger_message):
        messages.append(logger_message)

    logger = define_structured_logger('some_name', _append_message, level=DEBUG)
    context = ExecutionContext(loggers=[logger])
    context.debug('from_context', foo=2)
    assert len(messages) == 1
    message = messages[0]
    assert message.name == 'some_name'
    assert message.level == 'DEBUG'
    assert message.meta['foo'] == 2
    assert message.meta['orig_message'] == 'from_context'


from collections import namedtuple


class LogRecord:
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
        return EventType(event_type) if event_type else EventType.UNCATEGORIZED


class PipelineEventRecord(LogRecord):
    @property
    def pipeline_name(self):
        return self._logger_message.meta['pipeline']


class UncategorizedLogRecord(LogRecord):
    pass


EVENT_CLS_LOOKUP = {
    EventType.PIPELINE_START: PipelineEventRecord,
    EventType.PIPELINE_SUCCESS: PipelineEventRecord,
    EventType.PIPELINE_FAILURE: PipelineEventRecord,
}


def construct_typed_message(logger_message):
    event_type = logger_message.meta.get('event_type')
    if event_type:
        log_record_cls = EVENT_CLS_LOOKUP.get(EventType(event_type), UncategorizedLogRecord)
    else:
        log_record_cls = UncategorizedLogRecord

    return log_record_cls(logger_message)


def test_construct_typed_log_messages():
    messages = []

    def _append_message(logger_message):
        messages.append(construct_typed_message(logger_message))

    logger = define_structured_logger('some_name', _append_message, level=DEBUG)
    context = ExecutionContext(loggers=[logger])
    context.info('random message')

    assert len(messages) == 1
    message = messages[0]
    assert isinstance(message, UncategorizedLogRecord)

    with context.value('pipeline', 'some_pipeline'):
        context.events.pipeline_start()

    assert len(messages) == 2
    pipeline_start = messages[1]
    assert isinstance(pipeline_start, PipelineEventRecord)
    assert pipeline_start.event_type == EventType.PIPELINE_START