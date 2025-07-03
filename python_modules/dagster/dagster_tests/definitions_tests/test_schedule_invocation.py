import datetime
from typing import cast

import dagster as dg
import pytest
from dagster._core.storage.tags import PARTITION_NAME_TAG


def cron_test_schedule_factory_context():
    @dg.schedule(cron_schedule="* * * * *", job_name="no_pipeline")
    def basic_schedule(_):
        return {}

    return basic_schedule


def cron_test_schedule_factory_no_context():
    @dg.schedule(cron_schedule="* * * * *", job_name="no_pipeline")
    def basic_schedule():
        return {}

    return basic_schedule


def test_cron_schedule_invocation_all_args():
    basic_schedule_context = cron_test_schedule_factory_context()

    assert basic_schedule_context(None) == {}
    assert basic_schedule_context(dg.build_schedule_context()) == {}
    assert basic_schedule_context(_=None) == {}
    assert basic_schedule_context(_=dg.build_schedule_context()) == {}

    basic_schedule_no_context = cron_test_schedule_factory_no_context()

    assert basic_schedule_no_context() == {}


def test_incorrect_cron_schedule_invocation():
    basic_schedule = cron_test_schedule_factory_context()

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "Schedule evaluation function expected context argument, but no context argument was "
            "provided when invoking."
        ),
    ):
        basic_schedule()

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match="Schedule invocation expected argument '_'.",
    ):
        basic_schedule(foo=None)


def test_instance_access():
    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Attempted to initialize dagster instance, but no instance reference was provided.",
    ):
        dg.build_schedule_context().instance  # noqa: B018

    with dg.instance_for_test() as instance:
        assert isinstance(dg.build_schedule_context(instance).instance, dg.DagsterInstance)


def test_schedule_invocation_resources() -> None:
    class MyResource(dg.ConfigurableResource):
        a_str: str

    @dg.schedule(job_name="foo_job", cron_schedule="* * * * *")
    def basic_schedule_resource_req(my_resource: MyResource):
        return dg.RunRequest(run_key=None, run_config={"foo": my_resource.a_str}, tags={})

    # Test no arg invocation
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "Resource with key 'my_resource' required by schedule 'basic_schedule_resource_req' was"
            " not provided."
        ),
    ):
        basic_schedule_resource_req()

    # Test no resource provided
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "Resource with key 'my_resource' required by schedule 'basic_schedule_resource_req' was"
            " not provided."
        ),
    ):
        basic_schedule_resource_req(dg.build_schedule_context())

    assert hasattr(
        dg.build_schedule_context(resources={"my_resource": MyResource(a_str="foo")}).resources,
        "my_resource",
    )

    # Just need to pass context, which splats out into resource parameters
    assert cast(
        "dg.RunRequest",
        basic_schedule_resource_req(
            dg.build_schedule_context(resources={"my_resource": MyResource(a_str="foo")})
        ),
    ).run_config == {"foo": "foo"}


def test_schedule_invocation_resources_direct() -> None:
    class MyResource(dg.ConfigurableResource):
        a_str: str

    # Test no arg invocation
    @dg.schedule(job_name="foo_job", cron_schedule="* * * * *")
    def basic_schedule_resource_req(my_resource: MyResource):
        return dg.RunRequest(run_key=None, run_config={"foo": my_resource.a_str}, tags={})

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "Resource with key 'my_resource' required by schedule 'basic_schedule_resource_req' was"
            " not provided."
        ),
    ):
        basic_schedule_resource_req()

    # Can pass resource through context
    assert cast(
        "dg.RunRequest",
        basic_schedule_resource_req(
            context=dg.build_schedule_context(resources={"my_resource": MyResource(a_str="foo")})
        ),
    ).run_config == {"foo": "foo"}

    # Can pass resource directly
    assert cast(
        "dg.RunRequest",
        basic_schedule_resource_req(my_resource=MyResource(a_str="foo")),
    ).run_config == {"foo": "foo"}

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "If directly invoking a schedule, you may not provide resources as"
            " positional"
            " arguments, only as keyword arguments."
        ),
    ):
        # We don't allow providing resources as args, this adds too much complexity
        # They must be kwargs, and we will error accordingly
        assert cast(
            "dg.RunRequest",
            basic_schedule_resource_req(MyResource(a_str="foo")),
        ).run_config == {"foo": "foo"}

    # Can pass resource directly with context
    assert cast(
        "dg.RunRequest",
        basic_schedule_resource_req(
            dg.build_schedule_context(), my_resource=MyResource(a_str="foo")
        ),
    ).run_config == {"foo": "foo"}

    # Test with context arg requirement
    @dg.schedule(job_name="foo_job", cron_schedule="* * * * *")
    def basic_schedule_with_context_resource_req(my_resource: MyResource, context):
        return dg.RunRequest(run_key=None, run_config={"foo": my_resource.a_str}, tags={})

    assert cast(
        "dg.RunRequest",
        basic_schedule_with_context_resource_req(
            dg.build_schedule_context(), my_resource=MyResource(a_str="foo")
        ),
    ).run_config == {"foo": "foo"}


def test_recreating_schedule_with_resource_arg() -> None:
    class MyResource(dg.ConfigurableResource):
        a_str: str

    @dg.schedule(job_name="foo_job", cron_schedule="* * * * *")
    def basic_schedule_with_context_resource_req(my_resource: MyResource, context):
        return dg.RunRequest(run_key=None, run_config={"foo": my_resource.a_str}, tags={})

    @dg.job
    def junk_job():
        pass

    updated_schedule = basic_schedule_with_context_resource_req.with_updated_job(junk_job)

    assert cast(
        "dg.RunRequest",
        updated_schedule(dg.build_schedule_context(), my_resource=MyResource(a_str="foo")),
    ).run_config == {"foo": "foo"}


def test_schedule_invocation_resources_direct_many() -> None:
    class MyResource(dg.ConfigurableResource):
        a_str: str

    # Test no arg invocation
    @dg.schedule(job_name="foo_job", cron_schedule="* * * * *")
    def basic_schedule_resource_req(my_resource: MyResource, my_other_resource: MyResource):
        return dg.RunRequest(
            run_key=None,
            run_config={"foo": my_resource.a_str, "bar": my_other_resource.a_str},
            tags={},
        )

    # Can pass resource directly
    assert cast(
        "dg.RunRequest",
        basic_schedule_resource_req(
            my_other_resource=MyResource(a_str="bar"), my_resource=MyResource(a_str="foo")
        ),
    ).run_config == {"foo": "foo", "bar": "bar"}

    # Can pass resources both directly and in context
    assert cast(
        "dg.RunRequest",
        basic_schedule_resource_req(
            context=dg.build_schedule_context(
                resources={"my_other_resource": MyResource(a_str="bar")}
            ),
            my_resource=MyResource(a_str="foo"),
        ),
    ).run_config == {"foo": "foo", "bar": "bar"}


def test_partition_key_run_request_schedule():
    @dg.job(partitions_def=dg.StaticPartitionsDefinition(["a"]))
    def my_job():
        pass

    @dg.schedule(cron_schedule="* * * * *", job_name="my_job")
    def my_schedule():
        return dg.RunRequest(partition_key="a")

    @dg.repository
    def my_repo():
        return [my_job, my_schedule]

    with dg.build_schedule_context(
        repository_def=my_repo, scheduled_execution_time=datetime.datetime(2023, 1, 1)
    ) as context:
        run_requests = my_schedule.evaluate_tick(context).run_requests
        assert len(run_requests) == 1  # pyright: ignore[reportArgumentType]
        run_request = run_requests[0]  # pyright: ignore[reportOptionalSubscript]
        assert run_request.tags.get(PARTITION_NAME_TAG) == "a"


def test_dynamic_partition_run_request_schedule():
    @dg.job(partitions_def=dg.DynamicPartitionsDefinition(lambda _: ["1"]))
    def my_job():
        pass

    @dg.schedule(cron_schedule="* * * * *", job_name="my_job")
    def my_schedule():
        yield dg.RunRequest(partition_key="1", run_key="1")
        yield my_job.run_request_for_partition(partition_key="1", run_key="2")

    @dg.repository
    def my_repo():
        return [my_job, my_schedule]

    with dg.build_schedule_context(
        repository_def=my_repo, scheduled_execution_time=datetime.datetime(2023, 1, 1)
    ) as context:
        run_requests = my_schedule.evaluate_tick(context).run_requests
        assert len(run_requests) == 2  # pyright: ignore[reportArgumentType]
        for request in run_requests:  # pyright: ignore[reportOptionalIterable]
            assert request.tags.get(PARTITION_NAME_TAG) == "1"


def test_logging():
    @dg.schedule(cron_schedule="* * * * *", job_name="no_pipeline")
    def logs(context):
        context.log.info("hello there")
        return {}

    ctx = dg.build_schedule_context()

    logs.evaluate_tick(ctx)
