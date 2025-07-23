import logging
import warnings

import dagster as dg
from dagster import DagsterInstance
from dagster._core.storage.tags import MAX_RETRIES_TAG, RETRY_ON_ASSET_OR_OP_FAILURE_TAG
from dagster._core.utils import coerce_valid_log_level
from dagster._utils.tags import normalize_tags


def test_basic_job():
    @dg.op
    def basic():
        pass

    @dg.job
    def basic_job():
        basic()

    assert isinstance(basic_job, dg.JobDefinition)


def test_job_resources():
    called = {}

    @dg.op(required_resource_keys={"foo"})
    def basic(context):
        called["basic"] = context.resources.foo

    @dg.resource
    def foo():
        return "foo"

    @dg.job(resource_defs={"foo": foo})
    def basic_job():
        basic()

    basic_job.execute_in_process()
    assert called["basic"] == "foo"


def test_job_config():
    called = {}

    @dg.op(config_schema={"foo": str})
    def basic(context):
        called["basic"] = context.op_config["foo"]

    @dg.job(config={"ops": {"basic": {"config": {"foo": "foo"}}}})
    def basic_job():
        basic()

    basic_job.execute_in_process()
    assert called["basic"] == "foo"


def test_job_config_mapping():
    @dg.op(config_schema=str)
    def my_op(context):
        return context.op_config

    def _config_fn(outer):
        return {"ops": {"my_op": {"config": outer["foo_schema"]}}}

    config_mapping = dg.ConfigMapping(config_fn=_config_fn, config_schema={"foo_schema": str})

    @dg.job(config=config_mapping)
    def my_job():
        my_op()

    result = my_job.execute_in_process(run_config={"foo_schema": "foo"})
    assert result.success
    assert result.output_for_node("my_op") == "foo"


def test_job_tags():
    @dg.op
    def basic():
        pass

    @dg.job(tags={"my_tag": "yes"})
    def job_with_tags():
        basic()

    assert job_with_tags.tags == {"my_tag": "yes"}
    assert job_with_tags.run_tags == {"my_tag": "yes"}

    @dg.job(tags={"my_tag": "yes"}, run_tags={"my_run_tag": "yes"})
    def job_with_tags_and_run_tags():
        basic()

    assert job_with_tags_and_run_tags.tags == {"my_tag": "yes"}
    assert job_with_tags_and_run_tags.run_tags == {"my_run_tag": "yes"}

    with DagsterInstance.ephemeral() as instance:
        result = job_with_tags.execute_in_process(instance=instance)
        assert result.success
        run = instance.get_runs()[0]
        assert run.tags.get("my_tag") == "yes"

        result = job_with_tags_and_run_tags.execute_in_process(instance=instance)
        assert result.success
        run = instance.get_runs()[0]
        assert "my_tag" not in run.tags
        assert run.tags.get("my_run_tag") == "yes"


def test_job_system_tags():
    @dg.op
    def basic():
        pass

    @dg.job(tags={MAX_RETRIES_TAG: 5, RETRY_ON_ASSET_OR_OP_FAILURE_TAG: False})
    def basic_job():
        basic()

    normalize_tags(basic_job.tags, allow_private_system_tags=False)


def test_invalid_tag_keys():
    @dg.op
    def basic():
        pass

    # turn off any outer warnings filters, e.g. ignores that are set in pyproject.toml
    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as caught_warnings:

        @dg.job(tags={"my_tag&": "yes", "my_tag#": "yes"})
        def basic_job():
            basic()

        warning = caught_warnings[0]
        assert "Non-compliant tag keys like ['my_tag&', 'my_tag#'] are deprecated" in str(
            warning.message
        )
        assert warning.filename.endswith("test_job.py")

    with DagsterInstance.ephemeral() as instance:
        result = basic_job.execute_in_process(instance=instance)
        assert result.success
        run = instance.get_runs()[0]
        assert run.tags.get("my_tag&") == "yes"


def test_job_logger():
    called = {}

    @dg.op
    def basic():
        pass

    @dg.logger(config_schema=dg.Field(str))
    def basic_logger(context):
        called["basic_logger"] = context.logger_config
        return logging.Logger("test", level=coerce_valid_log_level("INFO"))

    @dg.job(
        logger_defs={"basic_logger": basic_logger},
    )
    def basic_job():
        basic()

    basic_job.execute_in_process(
        run_config={"loggers": {"basic_logger": {"config": "hullo"}}},
    )
    assert called["basic_logger"] == "hullo"
