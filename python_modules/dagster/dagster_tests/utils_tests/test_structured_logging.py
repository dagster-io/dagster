import logging

from dagster.utils.logging import define_structured_logger

from dagster.core.events.logging import construct_event_record, LogMessageRecord

from dagster.utils.test import create_test_pipeline_execution_context


def test_structured_logger_in_context():
    messages = []

    def _append_message(logger_message):
        messages.append(logger_message)

    logger = define_structured_logger('some_name', _append_message, level=logging.DEBUG)
    context = create_test_pipeline_execution_context(loggers=[logger])
    context.log.debug('from_context', foo=2)
    assert len(messages) == 1
    message = messages[0]
    assert message.name == 'some_name'
    assert message.level == logging.DEBUG
    assert message.meta['foo'] == 2
    assert message.meta['orig_message'] == 'from_context'


def test_construct_event_record():
    messages = []

    def _append_message(logger_message):
        messages.append(construct_event_record(logger_message))

    logger = define_structured_logger('some_name', _append_message, level=logging.DEBUG)
    context = create_test_pipeline_execution_context(
        loggers=[logger], tags={'pipeline': 'some_pipeline'}
    )
    context.log.info('random message')

    assert len(messages) == 1
    message = messages[0]
    assert isinstance(message, LogMessageRecord)


def test_structured_logger_in_context_with_bad_log_level():
    messages = []

    def _append_message(logger_message):
        messages.append(logger_message)

    logger = define_structured_logger('some_name', _append_message, level=logging.DEBUG)
    context = create_test_pipeline_execution_context(loggers=[logger])
    context.log.gargle('from_context', foo=2)
    assert len(messages) == 1
    message = messages[0]
    assert message.name == 'some_name'
    assert message.level == logging.ERROR
    assert message.meta['foo'] == 2
    assert message.meta['orig_message'] == (
        'Unexpected log level: User code attempted to log at level \'GARGLE\', but no logger was '
        'configured to handle that level. Original message: \'from_context\''
    )
