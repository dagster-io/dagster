from collections import namedtuple
import logging
import uuid

from dagster.core.execution import ExecutionContext
from dagster.utils.logging import (DEBUG, INFO, WARNING, ERROR, CRITICAL)

LogMessage = namedtuple('LogMessage', 'msg extra level')

# eliminate complaint about overriding methods imprecisely
# pylint: disable=W0221


# weird name so that pytest ignores
class LoggerForTest(logging.Logger):
    def __init__(self, name=None):
        super(LoggerForTest, self).__init__(name if name else str(uuid.uuid4()))
        self.messages = []

    def debug(self, msg, *args, **kwargs):
        extra = kwargs.pop('extra', None)
        self.messages.append(LogMessage(msg=msg, level=DEBUG, extra=extra))

    def info(self, msg, *args, **kwargs):
        extra = kwargs.pop('extra', None)
        self.messages.append(LogMessage(msg=msg, level=INFO, extra=extra))

    def warning(self, msg, *args, **kwargs):
        extra = kwargs.pop('extra', None)
        self.messages.append(LogMessage(msg=msg, level=WARNING, extra=extra))

    def error(self, msg, *args, **kwargs):
        extra = kwargs.pop('extra', None)
        self.messages.append(LogMessage(msg=msg, level=ERROR, extra=extra))

    def critical(self, msg, *args, **kwargs):
        extra = kwargs.pop('extra', None)
        self.messages.append(LogMessage(msg=msg, level=CRITICAL, extra=extra))


def test_test_logger():
    logger = LoggerForTest()
    logger.debug('fog')
    assert len(logger.messages) == 1
    assert logger.messages[0] == LogMessage(msg='fog', level=DEBUG, extra=None)


def orig_message(message):
    return message.extra['orig_message']


def test_context_logging():
    logger = LoggerForTest()
    context = ExecutionContext(loggers=[logger])
    context.debug('debug from context')
    context.info('info from context')
    context.warning('warning from context')
    context.error('error from context')
    context.critical('critical from context')

    assert len(logger.messages) == 5

    assert logger.messages[0].level == DEBUG
    assert orig_message(logger.messages[0]) == 'debug from context'
    assert logger.messages[1].level == INFO
    assert orig_message(logger.messages[1]) == 'info from context'
    assert logger.messages[2].level == WARNING
    assert orig_message(logger.messages[2]) == 'warning from context'
    assert logger.messages[3].level == ERROR
    assert orig_message(logger.messages[3]) == 'error from context'
    assert logger.messages[4].level == CRITICAL
    assert orig_message(logger.messages[4]) == 'critical from context'


def test_context_value():
    logger = LoggerForTest()
    context = ExecutionContext(loggers=[logger])

    with context.value('some_key', 'some_value'):
        context.info('some message')

    assert logger.messages[0].extra['some_key'] == 'some_value'
    assert 'some_key="some_value"' in logger.messages[0].msg
    assert 'message="some message"' in logger.messages[0].msg


def test_get_context_value():
    context = ExecutionContext()

    with context.value('some_key', 'some_value'):
        assert context.get_context_value('some_key') == 'some_value'


def test_log_message_id():
    logger = LoggerForTest()
    context = ExecutionContext(loggers=[logger])
    context.info('something')

    assert isinstance(uuid.UUID(logger.messages[0].extra['log_message_id']), uuid.UUID)


def test_interleaved_context_value():
    logger = LoggerForTest()
    context = ExecutionContext(loggers=[logger])

    with context.value('key_one', 'value_one'):
        context.info('message one')
        with context.value('key_two', 'value_two'):
            context.info('message two')

    message_one = logger.messages[0]
    assert message_one.extra['key_one'] == 'value_one'
    assert 'key_two' not in message_one.extra
    assert 'key_one="value_one"' in message_one.msg
    assert 'key_two' not in message_one.msg

    message_two = logger.messages[1]
    assert message_two.extra['key_one'] == 'value_one'
    assert message_two.extra['key_two'] == 'value_two'
    assert 'key_one="value_one"' in message_two.msg
    assert 'key_two="value_two"' in message_two.msg


def test_message_specific_logging():
    logger = LoggerForTest()
    context = ExecutionContext(loggers=[logger])
    with context.value('key_one', 'value_one'):
        context.info('message one', key_two='value_two')

    message_one = logger.messages[0]
    assert message_one.extra['key_one'] == 'value_one'
    assert message_one.extra['key_two'] == 'value_two'

    assert set(message_one.extra.keys()) == set(
        ['key_one', 'key_two', 'log_message_id', 'orig_message']
    )


def test_multicontext_value():
    logger = LoggerForTest()
    context = ExecutionContext(loggers=[logger])
    with context.values({
        'key_one': 'value_one',
        'key_two': 'value_two',
    }):
        context.info('message one')

    message_two = logger.messages[0]
    assert message_two.extra['key_one'] == 'value_one'
    assert message_two.extra['key_two'] == 'value_two'
    assert 'key_one="value_one"' in message_two.msg
    assert 'key_two="value_two"' in message_two.msg
