import logging

import pytest
from dagster import Field, build_init_logger_context, graph, job, logger, op
from dagster._core.errors import DagsterInvalidConfigError, DagsterInvalidInvocationError
from dagster._core.utils import coerce_valid_log_level


def test_logger_invocation_arguments():
    @logger
    def foo_logger(_my_context):
        logger_ = logging.Logger("foo")
        return logger_

    # Check that proper error is thrown when logger def is invoked with no context arg.
    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            "Logger initialization function has context argument, but no context argument was "
            "provided when invoking."
        ),
    ):
        foo_logger()

    # Check that proper error is thrown when logger def is invoked with wrong context arg name
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Logger initialization expected argument '_my_context'",
    ):
        foo_logger(context=build_init_logger_context())

    # Check that proper error is thrown when logger def is invoked with too many args
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Initialization of logger received multiple arguments.",
    ):
        foo_logger(build_init_logger_context(), 5)

    ret_logger = foo_logger(build_init_logger_context())

    assert isinstance(ret_logger, logging.Logger)

    ret_logger = foo_logger(_my_context=build_init_logger_context())

    assert isinstance(ret_logger, logging.Logger)


def test_logger_with_config():
    @logger(int)
    def int_logger(init_context):
        logger_ = logging.Logger("foo")
        logger_.setLevel(coerce_valid_log_level(init_context.logger_config))
        return logger_

    with pytest.raises(DagsterInvalidConfigError, match="Error in config for logger"):
        int_logger(build_init_logger_context())

    with pytest.raises(
        DagsterInvalidConfigError, match="Error when applying config mapping for logger"
    ):
        conf_logger = int_logger.configured("foo")
        conf_logger(build_init_logger_context())

    ret_logger = int_logger(build_init_logger_context(logger_config=3))
    assert ret_logger.level == 3

    conf_logger = int_logger.configured(4)
    ret_logger = conf_logger(build_init_logger_context())
    assert ret_logger.level == 4


def test_logger_with_config_defaults():
    @logger(Field(str, default_value="foo", is_required=False))
    def str_logger(init_context):
        logger_ = logging.Logger(init_context.logger_config)
        return logger_

    logger_ = str_logger(None)
    assert logger_.name == "foo"

    logger_ = str_logger(build_init_logger_context())
    assert logger_.name == "foo"

    logger_ = str_logger(build_init_logger_context(logger_config="bar"))
    assert logger_.name == "bar"


def test_logger_mixed_config_defaults():
    @logger(
        {
            "foo_field": Field(str, default_value="foo", is_required=False),
            "bar_field": str,
        }
    )
    def str_logger(init_context):
        if init_context.logger_config["bar_field"] == "using_default":
            assert init_context.logger_config["foo_field"] == "foo"
        else:
            assert init_context.logger_config["bar_field"] == "not_using_default"
            assert init_context.logger_config["foo_field"] == "not_foo"
        logger_ = logging.Logger("test_logger")
        return logger_

    with pytest.raises(DagsterInvalidConfigError, match="Error in config for logger"):
        str_logger(build_init_logger_context())

    str_logger(build_init_logger_context(logger_config={"bar_field": "using_default"}))
    str_logger(
        build_init_logger_context(
            logger_config={"bar_field": "not_using_default", "foo_field": "not_foo"}
        )
    )


@op
def sample_op():
    return 1


@job
def sample_job():
    sample_op()


@op
def my_op():
    return 1


@graph
def sample_graph():
    my_op()


def test_logger_job_def():
    @logger  # pyright: ignore[reportCallIssue,reportArgumentType]
    def job_logger(init_context):
        assert init_context.job_def.name == "sample_job"

    job_logger(build_init_logger_context(job_def=sample_graph.to_job(name="sample_job")))
    job_logger(build_init_logger_context(job_def=sample_graph.to_job(name="sample_job")))

    with pytest.raises(AssertionError):
        job_logger(build_init_logger_context(job_def=sample_graph.to_job(name="foo")))
