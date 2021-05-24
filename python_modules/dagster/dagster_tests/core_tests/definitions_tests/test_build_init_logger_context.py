import logging

import pytest
from dagster import build_init_logger_context, logger
from dagster.core.errors import DagsterInvalidConfigError
from dagster.core.log_manager import coerce_valid_log_level


def test_basic_logger_init():
    @logger
    def foo_logger(_):
        logger_ = logging.Logger("foo")
        return logger_

    ret_logger = foo_logger.logger_fn(build_init_logger_context(foo_logger))

    assert isinstance(ret_logger, logging.Logger)


def test_logger_with_config():
    @logger(int)
    def int_logger(init_context):
        logger_ = logging.Logger("foo")
        logger_.setLevel(coerce_valid_log_level(init_context.logger_config))
        return logger_

    with pytest.raises(DagsterInvalidConfigError, match="Error in config for logger"):
        int_logger.logger_fn(build_init_logger_context(int_logger))

    with pytest.raises(DagsterInvalidConfigError, match="Error in config mapping for logger"):
        conf_logger = int_logger.configured("foo")
        conf_logger.logger_fn(build_init_logger_context(conf_logger))

    ret_logger = int_logger.logger_fn(build_init_logger_context(int_logger, logger_config=3))
    assert ret_logger.level == 3

    conf_logger = int_logger.configured(4)
    ret_logger = conf_logger.logger_fn(build_init_logger_context(conf_logger))
    assert ret_logger.level == 4
