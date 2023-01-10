import logging

from dagster import ConfigMapping, DagsterInstance, Field, JobDefinition, job, logger, op, resource
from dagster._core.utils import coerce_valid_log_level


def test_basic_job():
    @op
    def basic():
        pass

    @job
    def basic_job():
        basic()

    assert isinstance(basic_job, JobDefinition)


def test_job_resources():
    called = {}

    @op(required_resource_keys={"foo"})
    def basic(context):
        called["basic"] = context.resources.foo

    @resource
    def foo():
        return "foo"

    @job(resource_defs={"foo": foo})
    def basic_job():
        basic()

    basic_job.execute_in_process()
    assert called["basic"] == "foo"


def test_job_config():
    called = {}

    @op(config_schema={"foo": str})
    def basic(context):
        called["basic"] = context.op_config["foo"]

    @job(config={"ops": {"basic": {"config": {"foo": "foo"}}}})
    def basic_job():
        basic()

    basic_job.execute_in_process()
    assert called["basic"] == "foo"


def test_job_config_mapping():
    @op(config_schema=str)
    def my_op(context):
        return context.op_config

    def _config_fn(outer):
        return {"ops": {"my_op": {"config": outer["foo_schema"]}}}

    config_mapping = ConfigMapping(config_fn=_config_fn, config_schema={"foo_schema": str})

    @job(config=config_mapping)
    def my_job():
        my_op()

    result = my_job.execute_in_process(run_config={"foo_schema": "foo"})
    assert result.success
    assert result.output_for_node("my_op") == "foo"


def test_job_tags():
    @op
    def basic():
        pass

    @job(tags={"my_tag": "yes"})
    def basic_job():
        basic()

    with DagsterInstance.ephemeral() as instance:
        result = basic_job.execute_in_process(instance=instance)
        assert result.success
        run = instance.get_runs()[0]
        assert run.tags.get("my_tag") == "yes"


def test_job_logger():
    called = {}

    @op
    def basic():
        pass

    @logger(config_schema=Field(str))
    def basic_logger(context):
        called["basic_logger"] = context.logger_config
        return logging.Logger("test", level=coerce_valid_log_level("INFO"))

    @job(
        logger_defs={"basic_logger": basic_logger},
    )
    def basic_job():
        basic()

    basic_job.execute_in_process(
        run_config={"loggers": {"basic_logger": {"config": "hullo"}}},
    )
    assert called["basic_logger"] == "hullo"
