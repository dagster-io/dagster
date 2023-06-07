import datetime
from typing import cast

import pytest
from dagster import (
    DagsterInstance,
    DagsterInvariantViolationError,
    DynamicPartitionsDefinition,
    RunRequest,
    StaticPartitionsDefinition,
    build_schedule_context,
    job,
    repository,
    schedule,
)
from dagster._config.pythonic_config import ConfigurableResource
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvalidInvocationError
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._core.test_utils import instance_for_test


def cron_test_schedule_factory_context():
    @schedule(cron_schedule="* * * * *", job_name="no_pipeline")
    def basic_schedule(_):
        return {}

    return basic_schedule


def cron_test_schedule_factory_no_context():
    @schedule(cron_schedule="* * * * *", job_name="no_pipeline")
    def basic_schedule():
        return {}

    return basic_schedule


def test_cron_schedule_invocation_all_args():
    basic_schedule_context = cron_test_schedule_factory_context()

    assert basic_schedule_context(None) == {}
    assert basic_schedule_context(build_schedule_context()) == {}
    assert basic_schedule_context(_=None) == {}
    assert basic_schedule_context(_=build_schedule_context()) == {}

    basic_schedule_no_context = cron_test_schedule_factory_no_context()

    assert basic_schedule_no_context() == {}


def test_incorrect_cron_schedule_invocation():
    basic_schedule = cron_test_schedule_factory_context()

    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            "Schedule evaluation function expected context argument, but no context argument was "
            "provided when invoking."
        ),
    ):
        basic_schedule()

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Schedule invocation expected argument '_'.",
    ):
        basic_schedule(foo=None)


def test_instance_access():
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Attempted to initialize dagster instance, but no instance reference was provided.",
    ):
        build_schedule_context().instance  # noqa: B018

    with instance_for_test() as instance:
        assert isinstance(build_schedule_context(instance).instance, DagsterInstance)


def test_schedule_invocation_resources() -> None:
    class MyResource(ConfigurableResource):
        a_str: str

    @schedule(job_name="foo_job", cron_schedule="* * * * *")
    def basic_schedule_resource_req(my_resource: MyResource):
        return RunRequest(run_key=None, run_config={"foo": my_resource.a_str}, tags={})

    # Test no arg invocation
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "Resource with key 'my_resource' required by schedule 'basic_schedule_resource_req' was"
            " not provided."
        ),
    ):
        basic_schedule_resource_req()

    # Test no resource provided
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "Resource with key 'my_resource' required by schedule 'basic_schedule_resource_req' was"
            " not provided."
        ),
    ):
        basic_schedule_resource_req(build_schedule_context())

    assert hasattr(
        build_schedule_context(resources={"my_resource": MyResource(a_str="foo")}).resources,
        "my_resource",
    )

    # Just need to pass context, which splats out into resource parameters
    assert cast(
        RunRequest,
        basic_schedule_resource_req(
            build_schedule_context(resources={"my_resource": MyResource(a_str="foo")})
        ),
    ).run_config == {"foo": "foo"}


def test_schedule_invocation_resources_direct() -> None:
    class MyResource(ConfigurableResource):
        a_str: str

    # Test no arg invocation
    @schedule(job_name="foo_job", cron_schedule="* * * * *")
    def basic_schedule_resource_req(my_resource: MyResource):
        return RunRequest(run_key=None, run_config={"foo": my_resource.a_str}, tags={})

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "Resource with key 'my_resource' required by schedule 'basic_schedule_resource_req' was"
            " not provided."
        ),
    ):
        basic_schedule_resource_req()

    # Can pass resource through context
    assert cast(
        RunRequest,
        basic_schedule_resource_req(
            context=build_schedule_context(resources={"my_resource": MyResource(a_str="foo")})
        ),
    ).run_config == {"foo": "foo"}

    # Can pass resource directly
    assert cast(
        RunRequest,
        basic_schedule_resource_req(my_resource=MyResource(a_str="foo")),
    ).run_config == {"foo": "foo"}

    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            "If directly invoking a schedule, you may not provide resources as"
            " positional"
            " arguments, only as keyword arguments."
        ),
    ):
        # We don't allow providing resources as args, this adds too much complexity
        # They must be kwargs, and we will error accordingly
        assert cast(
            RunRequest,
            basic_schedule_resource_req(MyResource(a_str="foo")),
        ).run_config == {"foo": "foo"}

    # Can pass resource directly with context
    assert cast(
        RunRequest,
        basic_schedule_resource_req(build_schedule_context(), my_resource=MyResource(a_str="foo")),
    ).run_config == {"foo": "foo"}

    # Test with context arg requirement
    @schedule(job_name="foo_job", cron_schedule="* * * * *")
    def basic_schedule_with_context_resource_req(my_resource: MyResource, context):
        return RunRequest(run_key=None, run_config={"foo": my_resource.a_str}, tags={})

    assert cast(
        RunRequest,
        basic_schedule_with_context_resource_req(
            build_schedule_context(), my_resource=MyResource(a_str="foo")
        ),
    ).run_config == {"foo": "foo"}


def test_schedule_invocation_resources_direct_many() -> None:
    class MyResource(ConfigurableResource):
        a_str: str

    # Test no arg invocation
    @schedule(job_name="foo_job", cron_schedule="* * * * *")
    def basic_schedule_resource_req(my_resource: MyResource, my_other_resource: MyResource):
        return RunRequest(
            run_key=None,
            run_config={"foo": my_resource.a_str, "bar": my_other_resource.a_str},
            tags={},
        )

    # Can pass resource directly
    assert cast(
        RunRequest,
        basic_schedule_resource_req(
            my_other_resource=MyResource(a_str="bar"), my_resource=MyResource(a_str="foo")
        ),
    ).run_config == {"foo": "foo", "bar": "bar"}

    # Can pass resources both directly and in context
    assert cast(
        RunRequest,
        basic_schedule_resource_req(
            context=build_schedule_context(
                resources={"my_other_resource": MyResource(a_str="bar")}
            ),
            my_resource=MyResource(a_str="foo"),
        ),
    ).run_config == {"foo": "foo", "bar": "bar"}


def test_partition_key_run_request_schedule():
    @job(partitions_def=StaticPartitionsDefinition(["a"]))
    def my_job():
        pass

    @schedule(cron_schedule="* * * * *", job_name="my_job")
    def my_schedule():
        return RunRequest(partition_key="a")

    @repository
    def my_repo():
        return [my_job, my_schedule]

    with build_schedule_context(
        repository_def=my_repo, scheduled_execution_time=datetime.datetime(2023, 1, 1)
    ) as context:
        run_requests = my_schedule.evaluate_tick(context).run_requests
        assert len(run_requests) == 1
        run_request = run_requests[0]
        assert run_request.tags.get(PARTITION_NAME_TAG) == "a"


def test_dynamic_partition_run_request_schedule():
    @job(partitions_def=DynamicPartitionsDefinition(lambda _: ["1"]))
    def my_job():
        pass

    @schedule(cron_schedule="* * * * *", job_name="my_job")
    def my_schedule():
        yield RunRequest(partition_key="1", run_key="1")
        yield my_job.run_request_for_partition(partition_key="1", run_key="2")

    @repository
    def my_repo():
        return [my_job, my_schedule]

    with build_schedule_context(
        repository_def=my_repo, scheduled_execution_time=datetime.datetime(2023, 1, 1)
    ) as context:
        run_requests = my_schedule.evaluate_tick(context).run_requests
        assert len(run_requests) == 2
        for request in run_requests:
            assert request.tags.get(PARTITION_NAME_TAG) == "1"
