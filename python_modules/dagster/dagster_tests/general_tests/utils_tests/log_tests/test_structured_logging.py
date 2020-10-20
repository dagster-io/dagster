import logging
from contextlib import contextmanager

import pytest
from dagster.utils.log import define_structured_logger
from dagster.utils.test import create_test_pipeline_execution_context


@contextmanager
def construct_structured_logger(constructor=lambda x: x):
    messages = []

    def _append_message(logger_message):
        messages.append(constructor(logger_message))

    logger_def = define_structured_logger("some_name", _append_message, level=logging.DEBUG)
    yield logger_def, messages


def test_structured_logger_in_context():
    with construct_structured_logger() as (logger, messages):
        context = create_test_pipeline_execution_context(logger_defs={"structured_log": logger})
        context.log.debug("from_context", foo=2)
        assert len(messages) == 1
        message = messages[0]
        assert message.name == "some_name"
        assert message.level == logging.DEBUG
        assert message.meta["foo"] == 2
        assert message.meta["orig_message"] == "from_context"


def test_structured_logger_in_context_with_bad_log_level():
    messages = []

    def _append_message(logger_message):
        messages.append(logger_message)

    logger = define_structured_logger("some_name", _append_message, level=logging.DEBUG)
    context = create_test_pipeline_execution_context(logger_defs={"structured_logger": logger})
    with pytest.raises(AttributeError):
        context.log.gargle("from_context", foo=2)
