import logging

import pytest
from dagster import Field, build_init_logger_context, graph, logger, op, pipeline, solid
from dagster.check import CheckError
from dagster.core.errors import (
    DagsterInvalidConfigError,
    DagsterInvalidInvocationError,
    DagsterInvariantViolationError,
)
from dagster.core.utils import coerce_valid_log_level


def test_logger_invocation_arguments():
    @logger
    def foo_logger(_my_context):
        logger_ = logging.Logger("foo")
        return logger_

    # Check that proper error is thrown when logger def is invoked with no context arg.
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Logger initialization function has context argument, but no context argument was "
        "provided when invoking.",
    ):
        foo_logger()  # pylint: disable=no-value-for-parameter

    # Check that proper error is thrown when logger def is invoked with wrong context arg name
    with pytest.raises(
        DagsterInvalidInvocationError, match="Logger initialization expected argument '_my_context'"
    ):
        foo_logger(  # pylint: disable=unexpected-keyword-arg, no-value-for-parameter
            context=build_init_logger_context()
        )

    # Check that proper error is thrown when logger def is invoked with too many args
    with pytest.raises(
        DagsterInvalidInvocationError, match="Initialization of logger received multiple arguments."
    ):
        foo_logger(build_init_logger_context(), 5)  # pylint: disable=too-many-function-args

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

    with pytest.raises(DagsterInvalidConfigError, match="Error in config mapping for logger"):
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
    @logger({"foo_field": Field(str, default_value="foo", is_required=False), "bar_field": str})
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


@solid
def sample_solid():
    return 1


@pipeline
def sample_pipeline():
    sample_solid()


@op
def my_op():
    return 1


@graph
def sample_graph():
    my_op()


def test_logger_pipeline_def():
    @logger
    def pipe_logger(init_context):
        assert init_context.pipeline_def.name == "sample_pipeline"

    pipe_logger(build_init_logger_context(pipeline_def=sample_pipeline))

    with pytest.raises(AssertionError):
        pipe_logger(build_init_logger_context(pipeline_def=sample_graph.to_job()))


def test_logger_job_def():
    @logger
    def job_logger(init_context):
        assert init_context.job_def.name == "sample_job"

    job_logger(build_init_logger_context(job_def=sample_graph.to_job(name="sample_job")))
    job_logger(build_init_logger_context(pipeline_def=sample_graph.to_job(name="sample_job")))

    with pytest.raises(AssertionError):
        job_logger(build_init_logger_context(job_def=sample_graph.to_job(name="foo")))


def test_logger_both_def():
    with pytest.raises(CheckError, match="pipeline_def and job_def"):
        build_init_logger_context(pipeline_def=sample_pipeline, job_def=sample_graph.to_job())


def test_logger_context_get_job_from_pipeline_fails():
    @logger
    def job_logger(init_context):
        assert init_context.job_def.name == "sample_pipeline"

    with pytest.raises(DagsterInvariantViolationError, match="Please use .pipeline_def instead."):
        job_logger(build_init_logger_context(pipeline_def=sample_pipeline))
