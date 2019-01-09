from dagster.utils.logging import define_structured_logger, DEBUG

from dagster.core.events import (
    EventType,
    construct_event_record,
    LogMessageRecord,
    PipelineEventRecord,
)

from dagster.utils.test import create_test_runtime_execution_context


def test_structured_logger_in_context():
    messages = []

    def _append_message(logger_message):
        messages.append(logger_message)

    logger = define_structured_logger('some_name', _append_message, level=DEBUG)
    context = create_test_runtime_execution_context(loggers=[logger])
    context.debug('from_context', foo=2)
    assert len(messages) == 1
    message = messages[0]
    assert message.name == 'some_name'
    assert message.level == DEBUG
    assert message.meta['foo'] == 2
    assert message.meta['orig_message'] == 'from_context'


def test_construct_event_record():
    messages = []

    def _append_message(logger_message):
        messages.append(construct_event_record(logger_message))

    logger = define_structured_logger('some_name', _append_message, level=DEBUG)
    context = create_test_runtime_execution_context(loggers=[logger])
    context.info('random message')

    assert len(messages) == 1
    message = messages[0]
    assert isinstance(message, LogMessageRecord)

    with context.value('pipeline', 'some_pipeline'):
        context.events.pipeline_start()

    assert len(messages) == 2
    pipeline_start = messages[1]
    assert isinstance(pipeline_start, PipelineEventRecord)
    assert pipeline_start.event_type == EventType.PIPELINE_START
