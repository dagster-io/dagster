from dagster.utils.logging import define_structured_logger, DEBUG

from dagster.core.events.logging import construct_event_record, LogMessageRecord

from dagster.utils.test import create_test_pipeline_execution_context


def test_structured_logger_in_context():
    messages = []

    def _append_message(logger_message):
        messages.append(logger_message)

    logger = define_structured_logger('some_name', _append_message, level=DEBUG)
    context = create_test_pipeline_execution_context(loggers=[logger])
    context.log.debug('from_context', foo=2)
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
    context = create_test_pipeline_execution_context(
        loggers=[logger], tags={'pipeline': 'some_pipeline'}
    )
    context.log.info('random message')

    assert len(messages) == 1
    message = messages[0]
    assert isinstance(message, LogMessageRecord)
