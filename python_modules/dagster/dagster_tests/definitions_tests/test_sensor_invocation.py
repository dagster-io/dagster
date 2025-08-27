from collections.abc import Iterator
from contextlib import contextmanager
from typing import cast
from unittest import mock

import dagster as dg
import pytest
from dagster import AssetSelection, DagsterInstance, DagsterRunStatus, RunRequest, asset_sensor
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.storage.tags import PARTITION_NAME_TAG


def test_sensor_invocation_args():
    # Test no arg invocation
    @dg.sensor(job_name="foo_job")
    def basic_sensor_no_arg():
        return dg.RunRequest(run_key=None, run_config={}, tags={})

    assert basic_sensor_no_arg().run_config == {}  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]

    # Test underscore name
    @dg.sensor(job_name="foo_job")
    def basic_sensor(_):
        return dg.RunRequest(run_key=None, run_config={}, tags={})

    assert basic_sensor(dg.build_sensor_context()).run_config == {}  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
    assert basic_sensor(None).run_config == {}  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]

    # Test sensor arbitrary arg name
    @dg.sensor(job_name="foo_job")
    def basic_sensor_with_context(_arbitrary_context):
        return dg.RunRequest(run_key=None, run_config={}, tags={})

    context = dg.build_sensor_context()

    # Pass context as positional arg
    assert basic_sensor_with_context(context).run_config == {}  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]

    # pass context as kwarg
    assert basic_sensor_with_context(_arbitrary_context=context).run_config == {}  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]

    # pass context as wrong kwarg
    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match="Sensor invocation expected argument '_arbitrary_context'.",
    ):
        basic_sensor_with_context(bad_context=context)

    # pass context with no args
    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "Sensor evaluation function expected context argument, but no context argument was "
            "provided when invoking."
        ),
    ):
        basic_sensor_with_context()

    # pass context with too many args
    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "Sensor invocation received multiple non-resource arguments. Only a first positional"
            " context parameter should be provided when invoking."
        ),
    ):
        basic_sensor_with_context(context, _arbitrary_context=None)


def test_sensor_invocation_resources() -> None:
    class MyResource(dg.ConfigurableResource):
        a_str: str

    # Test no arg invocation
    @dg.sensor(job_name="foo_job")
    def basic_sensor_resource_req(my_resource: MyResource):
        return dg.RunRequest(run_key=None, run_config={"foo": my_resource.a_str}, tags={})

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "Resource with key 'my_resource' required by sensor 'basic_sensor_resource_req' was not"
            " provided."
        ),
    ):
        basic_sensor_resource_req()

    # Just need to pass context, which splats out into resource parameters
    assert cast(
        "dg.RunRequest",
        basic_sensor_resource_req(
            dg.build_sensor_context(resources={"my_resource": MyResource(a_str="foo")})
        ),
    ).run_config == {"foo": "foo"}


def test_sensor_invocation_resources_callable() -> None:
    class MyResource(dg.ConfigurableResource):
        a_str: str

    class Foo:
        def __call__(self, my_resource: MyResource):
            return dg.RunRequest(run_key=None, run_config={"foo": my_resource.a_str}, tags={})

    weird_sensor = dg.SensorDefinition(
        name="weird",
        evaluation_fn=Foo(),
    )

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=("Resource with key 'my_resource' required by sensor 'weird' was not provided."),
    ):
        weird_sensor()

    # Just need to pass context, which splats out into resource parameters
    assert cast(
        "dg.RunRequest",
        weird_sensor(dg.build_sensor_context(resources={"my_resource": MyResource(a_str="foo")})),
    ).run_config == {"foo": "foo"}


def test_sensor_invocation_resources_direct() -> None:
    class MyResource(dg.ConfigurableResource):
        a_str: str

    # Test no arg invocation
    @dg.sensor(job_name="foo_job")
    def basic_sensor_resource_req(my_resource: MyResource):
        return dg.RunRequest(run_key=None, run_config={"foo": my_resource.a_str}, tags={})

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "Resource with key 'my_resource' required by sensor 'basic_sensor_resource_req' was not"
            " provided."
        ),
    ):
        basic_sensor_resource_req()

    # Can pass resource through context
    assert cast(
        "dg.RunRequest",
        basic_sensor_resource_req(
            context=dg.build_sensor_context(resources={"my_resource": MyResource(a_str="foo")})
        ),
    ).run_config == {"foo": "foo"}

    # Can pass resource directly
    assert cast(
        "dg.RunRequest",
        basic_sensor_resource_req(my_resource=MyResource(a_str="foo")),
    ).run_config == {"foo": "foo"}

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "If directly invoking a sensor, you may not provide resources as"
            " positional"
            " arguments, only as keyword arguments."
        ),
    ):
        # We don't allow providing resources as args, this adds too much complexity
        # They must be kwargs, and we will error accordingly
        assert cast(
            "dg.RunRequest",
            basic_sensor_resource_req(MyResource(a_str="foo")),
        ).run_config == {"foo": "foo"}

    # Can pass resource directly with context
    assert cast(
        "dg.RunRequest",
        basic_sensor_resource_req(dg.build_sensor_context(), my_resource=MyResource(a_str="foo")),
    ).run_config == {"foo": "foo"}

    # Test with context arg requirement
    @dg.sensor(job_name="foo_job")
    def basic_sensor_with_context_resource_req(my_resource: MyResource, context):
        return dg.RunRequest(run_key=None, run_config={"foo": my_resource.a_str}, tags={})

    assert cast(
        "dg.RunRequest",
        basic_sensor_with_context_resource_req(
            dg.build_sensor_context(), my_resource=MyResource(a_str="foo")
        ),
    ).run_config == {"foo": "foo"}


def test_recreating_sensor_with_resource_arg() -> None:
    class MyResource(dg.ConfigurableResource):
        a_str: str

    @dg.sensor(job_name="foo_job")
    def basic_sensor_with_context_resource_req(my_resource: MyResource, context):
        return dg.RunRequest(run_key=None, run_config={"foo": my_resource.a_str}, tags={})

    @dg.job
    def junk_job():
        pass

    updated_sensor = basic_sensor_with_context_resource_req.with_updated_job(junk_job)

    assert cast(
        "dg.RunRequest",
        updated_sensor(dg.build_sensor_context(), my_resource=MyResource(a_str="foo")),
    ).run_config == {"foo": "foo"}


def test_sensor_invocation_resources_direct_many() -> None:
    class MyResource(dg.ConfigurableResource):
        a_str: str

    # Test no arg invocation
    @dg.sensor(job_name="foo_job")
    def basic_sensor_resource_req(my_resource: MyResource, my_other_resource: MyResource):
        return dg.RunRequest(
            run_key=None,
            run_config={"foo": my_resource.a_str, "bar": my_other_resource.a_str},
            tags={},
        )

    # Can pass resource directly
    assert cast(
        "dg.RunRequest",
        basic_sensor_resource_req(
            my_other_resource=MyResource(a_str="bar"), my_resource=MyResource(a_str="foo")
        ),
    ).run_config == {"foo": "foo", "bar": "bar"}

    # Pass resources both directly and in context
    assert cast(
        "dg.RunRequest",
        basic_sensor_resource_req(
            context=dg.build_sensor_context(
                resources={"my_other_resource": MyResource(a_str="bar")}
            ),
            my_resource=MyResource(a_str="foo"),
        ),
    ).run_config == {"foo": "foo", "bar": "bar"}


def test_sensor_invocation_resources_context_manager() -> None:
    @dg.sensor(job_name="foo_job")
    def basic_sensor_str_resource_req(my_resource: dg.ResourceParam[str]):
        return dg.RunRequest(run_key=None, run_config={"foo": my_resource}, tags={})

    @dg.resource
    @contextmanager
    def my_cm_resource(_) -> Iterator[str]:
        yield "foo"

    # Fails bc resource is a contextmanager and sensor context is not entered
    with pytest.raises(
        dg.DagsterInvariantViolationError, match="At least one provided resource is a generator"
    ) as exc_info:
        basic_sensor_str_resource_req(
            dg.build_sensor_context(resources={"my_resource": my_cm_resource})
        )

    assert "with build_sensor_context" in str(exc_info.value)
    with dg.build_sensor_context(resources={"my_resource": my_cm_resource}) as context:
        assert cast("dg.RunRequest", basic_sensor_str_resource_req(context)).run_config == {
            "foo": "foo"
        }


def test_sensor_invocation_resources_deferred() -> None:
    class MyResource(dg.ConfigurableResource):
        def create_resource(self, context) -> None:
            raise Exception()

    @dg.sensor(job_name="foo_job", required_resource_keys={"my_resource"})
    def basic_sensor_resource_req() -> dg.RunRequest:
        return dg.RunRequest(run_key=None, run_config={}, tags={})

    context = dg.build_sensor_context(resources={"my_resource": MyResource()})

    # Resource isn't created until sensor is invoked
    with pytest.raises(Exception):
        basic_sensor_resource_req(context)

    # Same goes for context manager
    with context as open_context:
        with pytest.raises(Exception):
            basic_sensor_resource_req(open_context)


def test_multi_asset_sensor_invocation_resources() -> None:
    class MyResource(dg.ConfigurableResource):
        a_str: str

    @dg.op
    def an_op():
        return 1

    @dg.job
    def the_job():
        an_op()

    @dg.asset
    def asset_a():
        return 1

    @dg.asset
    def asset_b():
        return 1

    @dg.multi_asset_sensor(
        monitored_assets=[dg.AssetKey("asset_a"), dg.AssetKey("asset_b")], job=the_job
    )
    def a_and_b_sensor(context, my_resource: MyResource):
        asset_events = context.latest_materialization_records_by_key()
        if all(asset_events.values()):
            context.advance_all_cursors()
            return dg.RunRequest(
                run_key=context.cursor, run_config={"foo": my_resource.a_str}, tags={}
            )

    @dg.repository
    def my_repo():
        return [asset_a, asset_b, a_and_b_sensor]

    with dg.instance_for_test() as instance:
        dg.materialize([asset_a, asset_b], instance=instance)
        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[dg.AssetKey("asset_a"), dg.AssetKey("asset_b")],
            instance=instance,
            repository_def=my_repo,
            resources={"my_resource": MyResource(a_str="bar")},
        )
        assert cast("dg.RunRequest", a_and_b_sensor(ctx)).run_config == {"foo": "bar"}


def test_multi_asset_sensor_with_source_assets() -> None:
    # upstream_asset1 exists in another repository
    @dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2023-03-01"))
    def upstream_asset1(): ...

    upstream_asset1_source = dg.SourceAsset(
        key=upstream_asset1.key,
        partitions_def=dg.DailyPartitionsDefinition(start_date="2023-03-01"),
    )

    @dg.asset()
    def downstream_asset(upstream_asset1): ...

    @dg.multi_asset_sensor(
        monitored_assets=[
            upstream_asset1.key,
        ],
        job=dg.define_asset_job("foo", selection=[downstream_asset]),
    )
    def my_sensor(context):
        run_requests = []
        for partition, record in context.latest_materialization_records_by_partition(
            dg.AssetKey("upstream_asset1")
        ).items():
            context.advance_cursor({upstream_asset1.key: record})
            run_requests.append(dg.RunRequest(partition_key=partition))
        return run_requests

    @dg.repository
    def my_repo():
        return [upstream_asset1_source, downstream_asset, my_sensor]

    with dg.instance_for_test() as instance:
        dg.materialize([upstream_asset1], instance=instance, partition_key="2023-03-01")
        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[dg.AssetKey("upstream_asset1")],
            instance=instance,
            repository_def=my_repo,
        )
        run_requests = cast("list[RunRequest]", my_sensor(ctx))
        assert len(run_requests) == 1
        assert run_requests[0].partition_key == "2023-03-01"


def test_run_status_sensor_invocation_resources() -> None:
    class MyResource(dg.ConfigurableResource):
        a_str: str

    @dg.run_status_sensor(run_status=DagsterRunStatus.SUCCESS)
    def status_sensor(context, my_resource: MyResource):
        assert context.dagster_event.event_type_value == "PIPELINE_SUCCESS"
        assert my_resource.a_str == "bar"

    @dg.run_status_sensor(run_status=DagsterRunStatus.SUCCESS)
    def status_sensor_no_context(my_resource: MyResource):
        assert my_resource.a_str == "bar"

    @dg.op
    def succeeds():
        return 1

    @dg.job
    def my_job_2():
        succeeds()

    instance = DagsterInstance.ephemeral()
    result = my_job_2.execute_in_process(instance=instance, raise_on_error=False)

    dagster_run = result.dagster_run
    dagster_event = result.get_run_success_event()

    context = dg.build_run_status_sensor_context(
        sensor_name="status_sensor",
        dagster_instance=instance,
        dagster_run=dagster_run,
        dagster_event=dagster_event,
        resources={"my_resource": MyResource(a_str="bar")},
    )

    status_sensor(context)
    status_sensor_no_context(context)


def test_run_status_sensor_invocation_resources_direct() -> None:
    class MyResource(dg.ConfigurableResource):
        a_str: str

    @dg.run_status_sensor(run_status=DagsterRunStatus.SUCCESS)
    def status_sensor(context, my_resource: MyResource):
        assert context.dagster_event.event_type_value == "PIPELINE_SUCCESS"
        assert my_resource.a_str == "bar"

    @dg.run_status_sensor(run_status=DagsterRunStatus.SUCCESS)
    def status_sensor_no_context(my_resource: MyResource):
        assert my_resource.a_str == "bar"

    @dg.op
    def succeeds():
        return 1

    @dg.job
    def my_job_2():
        succeeds()

    instance = DagsterInstance.ephemeral()
    result = my_job_2.execute_in_process(instance=instance, raise_on_error=False)

    dagster_run = result.dagster_run
    dagster_event = result.get_run_success_event()

    context = dg.build_run_status_sensor_context(
        sensor_name="status_sensor",
        dagster_instance=instance,
        dagster_run=dagster_run,
        dagster_event=dagster_event,
    )

    status_sensor(context, my_resource=MyResource(a_str="bar"))
    status_sensor_no_context(context, my_resource=MyResource(a_str="bar"))


def test_run_failure_sensor_invocation_resources() -> None:
    class MyResource(dg.ConfigurableResource):
        a_str: str

    @dg.run_failure_sensor
    def failure_sensor(context, my_resource: MyResource):
        assert context.dagster_event.event_type_value == "PIPELINE_SUCCESS"
        assert my_resource.a_str == "bar"

    @dg.run_failure_sensor
    def failure_sensor_no_context(my_resource: MyResource):
        assert my_resource.a_str == "bar"

    @dg.op
    def succeeds():
        return 1

    @dg.job
    def my_job_2():
        succeeds()

    instance = DagsterInstance.ephemeral()
    result = my_job_2.execute_in_process(instance=instance, raise_on_error=False)

    dagster_run = result.dagster_run
    dagster_event = result.get_run_success_event()

    context = dg.build_run_status_sensor_context(
        sensor_name="failure_sensor",
        dagster_instance=instance,
        dagster_run=dagster_run,
        dagster_event=dagster_event,
        resources={"my_resource": MyResource(a_str="bar")},
    ).for_run_failure()

    failure_sensor(context)
    failure_sensor_no_context(context)


def test_instance_access_built_sensor():
    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Attempted to initialize dagster instance, but no instance reference was provided.",
    ):
        dg.build_sensor_context().instance  # noqa: B018

    with dg.instance_for_test() as instance:
        assert isinstance(dg.build_sensor_context(instance).instance, dg.DagsterInstance)


def test_instance_access_with_mock():
    mock_instance = mock.MagicMock(spec=DagsterInstance)
    assert dg.build_sensor_context(instance=mock_instance).instance == mock_instance


def test_sensor_w_no_job():
    @dg.sensor()
    def no_job_sensor():
        return dg.RunRequest(
            run_key=None,
            run_config=None,
            tags=None,
        )

    with pytest.raises(
        Exception,
        match=r".* Sensor evaluation function returned a RunRequest for a sensor lacking a "
        r"specified target .*",
    ):
        with dg.build_sensor_context() as context:
            no_job_sensor.evaluate_tick(context)


def test_validated_partitions():
    @dg.job(partitions_def=dg.StaticPartitionsDefinition(["foo", "bar"]))
    def my_job():
        pass

    @dg.sensor(job=my_job)
    def invalid_req_sensor():
        return dg.RunRequest(partition_key="nonexistent")

    @dg.sensor(job=my_job)
    def valid_req_sensor():
        return dg.RunRequest(partition_key="foo", tags={"yay": "yay!"})

    @dg.repository
    def my_repo():
        return [my_job, invalid_req_sensor, valid_req_sensor]

    with pytest.raises(dg.DagsterInvariantViolationError, match="Must provide repository def"):
        with dg.build_sensor_context() as context:
            invalid_req_sensor.evaluate_tick(context)

    with pytest.raises(dg.DagsterUnknownPartitionError, match="Could not find a partition"):
        with dg.build_sensor_context(repository_def=my_repo) as context:
            invalid_req_sensor.evaluate_tick(context)

    with dg.build_sensor_context(repository_def=my_repo) as context:
        run_requests = valid_req_sensor.evaluate_tick(context).run_requests
        assert len(run_requests) == 1  # pyright: ignore[reportArgumentType]
        run_request = run_requests[0]  # pyright: ignore[reportOptionalSubscript]
        assert run_request.partition_key == "foo"
        assert run_request.run_config == {}
        assert run_request.tags.get(PARTITION_NAME_TAG) == "foo"
        assert run_request.tags.get("yay") == "yay!"
        assert run_request.tags.get("dagster/sensor_name") == "valid_req_sensor"


def test_partitioned_config_run_request():
    def partition_fn(partition_key: str):
        return {"ops": {"my_op": {"config": {"partition": partition_key}}}}

    @dg.static_partitioned_config(partition_keys=["a", "b", "c", "d"])
    def my_partitioned_config(partition_key: str):
        return partition_fn(partition_key)

    @dg.op
    def my_op():
        pass

    @dg.job(config=my_partitioned_config)
    def my_job():
        my_op()

    @dg.sensor(job=my_job)
    def valid_req_sensor():
        return dg.RunRequest(partition_key="a", tags={"yay": "yay!"})

    @dg.sensor(job=my_job)
    def invalid_req_sensor():
        return dg.RunRequest(partition_key="nonexistent")

    @dg.sensor(job_name="my_job")
    def job_str_target_sensor():
        return dg.RunRequest(partition_key="a", tags={"yay": "yay!"})

    @dg.sensor(job_name="my_job")
    def invalid_job_str_target_sensor():
        return dg.RunRequest(partition_key="invalid")

    @dg.repository
    def my_repo():
        return [
            my_job,
            valid_req_sensor,
            invalid_req_sensor,
            job_str_target_sensor,
            invalid_job_str_target_sensor,
        ]

    with dg.build_sensor_context(repository_def=my_repo) as context:
        for valid_sensor in [valid_req_sensor, job_str_target_sensor]:
            run_requests = valid_sensor.evaluate_tick(context).run_requests
            assert len(run_requests) == 1  # pyright: ignore[reportArgumentType]
            run_request = run_requests[0]  # pyright: ignore[reportOptionalSubscript]
            assert run_request.run_config == partition_fn("a")
            assert run_request.tags.get(PARTITION_NAME_TAG) == "a"
            assert run_request.tags.get("yay") == "yay!"

        for invalid_sensor in [invalid_req_sensor, invalid_job_str_target_sensor]:
            with pytest.raises(dg.DagsterUnknownPartitionError, match="Could not find a partition"):
                run_requests = invalid_sensor.evaluate_tick(context).run_requests


def test_asset_selection_run_request_partition_key():
    @dg.sensor(asset_selection=AssetSelection.assets("a_asset"))
    def valid_req_sensor():
        return dg.RunRequest(partition_key="a")

    @dg.sensor(asset_selection=AssetSelection.assets("a_asset"))
    def invalid_req_sensor():
        return dg.RunRequest(partition_key="b")

    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["a"]))
    def a_asset():
        return 1

    daily_partitions_def = dg.DailyPartitionsDefinition("2023-01-01")

    @dg.asset(partitions_def=daily_partitions_def)
    def b_asset():
        return 1

    @dg.asset(partitions_def=daily_partitions_def)
    def c_asset():
        return 1

    @dg.repository
    def my_repo():
        return [
            a_asset,
            b_asset,
            c_asset,
            valid_req_sensor,
            invalid_req_sensor,
            dg.define_asset_job("a_job", [a_asset]),
            dg.define_asset_job("b_job", [b_asset]),
        ]

    with dg.build_sensor_context(repository_def=my_repo) as context:
        run_requests = valid_req_sensor.evaluate_tick(context).run_requests
        assert len(run_requests) == 1  # pyright: ignore[reportArgumentType]
        assert run_requests[0].partition_key == "a"  # pyright: ignore[reportOptionalSubscript]
        assert run_requests[0].tags.get(PARTITION_NAME_TAG) == "a"  # pyright: ignore[reportOptionalSubscript]
        assert run_requests[0].asset_selection == [a_asset.key]  # pyright: ignore[reportOptionalSubscript]

        with pytest.raises(dg.DagsterUnknownPartitionError, match="Could not find a partition"):
            invalid_req_sensor.evaluate_tick(context)


def test_run_status_sensor():
    @dg.run_status_sensor(run_status=DagsterRunStatus.SUCCESS)
    def status_sensor(context):
        assert context.dagster_event.event_type_value == "PIPELINE_SUCCESS"

    @dg.op
    def succeeds():
        return 1

    @dg.job
    def my_job_2():
        succeeds()

    instance = DagsterInstance.ephemeral()
    result = my_job_2.execute_in_process(instance=instance, raise_on_error=False)

    dagster_run = result.dagster_run
    dagster_event = result.get_run_success_event()

    context = dg.build_run_status_sensor_context(
        sensor_name="status_sensor",
        dagster_instance=instance,
        dagster_run=dagster_run,
        dagster_event=dagster_event,
    )

    status_sensor(context)


def test_run_failure_sensor():
    @dg.run_failure_sensor
    def failure_sensor(context):
        assert context.dagster_event.event_type_value == "PIPELINE_FAILURE"

    @dg.op
    def will_fail():
        raise Exception("failure")

    @dg.job
    def my_job():
        will_fail()

    instance = DagsterInstance.ephemeral()
    result = my_job.execute_in_process(instance=instance, raise_on_error=False)

    dagster_run = result.dagster_run
    dagster_event = result.get_run_failure_event()

    context = dg.build_run_status_sensor_context(
        sensor_name="failure_sensor",
        dagster_instance=instance,
        dagster_run=dagster_run,
        dagster_event=dagster_event,
    ).for_run_failure()

    failure_sensor(context)


def test_run_status_sensor_run_request():
    @dg.op
    def succeeds():
        return 1

    @dg.job
    def my_job_2():
        succeeds()

    instance = DagsterInstance.ephemeral()
    result = my_job_2.execute_in_process(instance=instance, raise_on_error=False)

    dagster_run = result.dagster_run
    dagster_event = result.get_run_success_event()

    context = dg.build_run_status_sensor_context(
        sensor_name="status_sensor",
        dagster_instance=instance,
        dagster_run=dagster_run,
        dagster_event=dagster_event,
    )

    @dg.run_status_sensor(run_status=DagsterRunStatus.SUCCESS)
    def basic_sensor(_):
        return dg.RunRequest(run_key=None, run_config={}, tags={})

    assert basic_sensor(context).run_config == {}  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]

    # test with context
    @dg.run_status_sensor(run_status=DagsterRunStatus.SUCCESS)
    def basic_sensor_w_arg(context):
        assert context.dagster_event.event_type_value == "PIPELINE_SUCCESS"
        return dg.RunRequest(run_key=None, run_config={}, tags={})

    assert basic_sensor_w_arg(context).run_config == {}  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]


def test_run_failure_w_run_request():
    @dg.op
    def will_fail():
        raise Exception("failure")

    @dg.job
    def my_job():
        will_fail()

    instance = DagsterInstance.ephemeral()
    result = my_job.execute_in_process(instance=instance, raise_on_error=False)

    dagster_run = result.dagster_run
    dagster_event = result.get_run_failure_event()

    context = dg.build_run_status_sensor_context(
        sensor_name="failure_sensor",
        dagster_instance=instance,
        dagster_run=dagster_run,
        dagster_event=dagster_event,
    ).for_run_failure()

    # Test no arg invocation
    @dg.run_failure_sensor
    def basic_sensor(_):
        return dg.RunRequest(run_key=None, run_config={}, tags={})

    assert basic_sensor(context).run_config == {}  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]

    # test with context
    @dg.run_failure_sensor
    def basic_sensor_w_arg(context):
        assert context.dagster_event.event_type_value == "PIPELINE_FAILURE"
        return dg.RunRequest(run_key=None, run_config={}, tags={})

    assert basic_sensor_w_arg(context).run_config == {}  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]


def test_multi_asset_sensor():
    @dg.op
    def an_op():
        return 1

    @dg.job
    def the_job():
        an_op()

    @dg.asset
    def asset_a():
        return 1

    @dg.asset
    def asset_b():
        return 1

    @dg.multi_asset_sensor(
        monitored_assets=[dg.AssetKey("asset_a"), dg.AssetKey("asset_b")], job=the_job
    )
    def a_and_b_sensor(context):
        asset_events = context.latest_materialization_records_by_key()
        if all(asset_events.values()):
            context.advance_all_cursors()
            return dg.RunRequest(run_key=context.cursor, run_config={})

    defs = dg.Definitions(assets=[asset_a, asset_b], sensors=[a_and_b_sensor])
    my_repo = defs.get_repository_def()

    for definitions, repository_def in [(defs, None), (None, my_repo)]:
        with dg.instance_for_test() as instance:
            dg.materialize([asset_a, asset_b], instance=instance)
            ctx = dg.build_multi_asset_sensor_context(
                monitored_assets=[dg.AssetKey("asset_a"), dg.AssetKey("asset_b")],
                instance=instance,
                repository_def=repository_def,
                definitions=definitions,
            )
            assert a_and_b_sensor(ctx).run_config == {}  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]


def test_multi_asset_sensor_selection():
    @dg.multi_asset(outs={"a": dg.AssetOut(key="asset_a"), "b": dg.AssetOut(key="asset_b")})
    def two_assets():
        return 1, 2

    @dg.multi_asset_sensor(monitored_assets=[dg.AssetKey("asset_a")])
    def passing_sensor(context):
        pass

    @dg.repository
    def my_repo():
        return [two_assets, passing_sensor]


def test_multi_asset_sensor_has_assets():
    @dg.multi_asset(outs={"a": dg.AssetOut(key="asset_a"), "b": dg.AssetOut(key="asset_b")})
    def two_assets():
        return 1, 2

    @dg.multi_asset_sensor(monitored_assets=[dg.AssetKey("asset_a"), dg.AssetKey("asset_b")])
    def passing_sensor(context):
        assert context.assets_defs_by_key[dg.AssetKey("asset_a")].keys == two_assets.keys
        assert context.assets_defs_by_key[dg.AssetKey("asset_b")].keys == two_assets.keys
        assert len(context.assets_defs_by_key) == 2

    @dg.repository
    def my_repo():
        return [two_assets, passing_sensor]

    with dg.instance_for_test() as instance:
        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[dg.AssetKey("asset_a"), dg.AssetKey("asset_b")],
            instance=instance,
            repository_def=my_repo,
        )
        passing_sensor(ctx)


def test_partitions_multi_asset_sensor_context():
    daily_partitions_def = dg.DailyPartitionsDefinition("2020-01-01")

    @dg.asset(partitions_def=daily_partitions_def)
    def daily_partitions_asset():
        return 1

    @dg.asset(partitions_def=daily_partitions_def)
    def daily_partitions_asset_2():
        return 1

    @dg.repository
    def my_repo():
        return [daily_partitions_asset, daily_partitions_asset_2]

    asset_job = dg.define_asset_job(
        "yay", selection="daily_partitions_asset", partitions_def=daily_partitions_def
    )

    @dg.multi_asset_sensor(
        monitored_assets=[daily_partitions_asset.key, daily_partitions_asset_2.key], job=asset_job
    )
    def two_asset_sensor(context):
        partition_1 = next(
            iter(
                context.latest_materialization_records_by_partition(
                    daily_partitions_asset.key
                ).keys()
            )
        )
        partition_2 = next(
            iter(
                context.latest_materialization_records_by_partition(
                    daily_partitions_asset_2.key
                ).keys()
            )
        )

        if partition_1 == partition_2:
            context.advance_all_cursors()
            return asset_job.run_request_for_partition(partition_1, run_key=None)

    with dg.instance_for_test() as instance:
        dg.materialize(
            [daily_partitions_asset, daily_partitions_asset_2],
            partition_key="2022-08-01",
            instance=instance,
        )
        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[daily_partitions_asset.key, daily_partitions_asset_2.key],
            instance=instance,
            repository_def=my_repo,
        )
        sensor_data = two_asset_sensor.evaluate_tick(ctx)
        assert len(sensor_data.run_requests) == 1  # pyright: ignore[reportArgumentType]
        assert sensor_data.run_requests[0].partition_key == "2022-08-01"  # pyright: ignore[reportOptionalSubscript]
        assert sensor_data.run_requests[0].tags["dagster/partition"] == "2022-08-01"  # pyright: ignore[reportOptionalSubscript]
        assert (
            ctx.cursor == '{"AssetKey([\'daily_partitions_asset\'])": ["2022-08-01", 4, {}],'
            ' "AssetKey([\'daily_partitions_asset_2\'])": ["2022-08-01", 5, {}]}'
        )


@dg.asset(partitions_def=dg.DailyPartitionsDefinition("2022-07-01"))
def july_asset():
    return 1


@dg.asset(partitions_def=dg.DailyPartitionsDefinition("2022-07-01"))
def july_asset_2():
    return 1


@dg.asset(partitions_def=dg.DailyPartitionsDefinition("2022-08-01"))
def august_asset():
    return 1


@dg.repository
def my_repo():
    return [july_asset, july_asset_2, august_asset]


def test_multi_asset_sensor_after_cursor_partition_flag():
    @dg.multi_asset_sensor(monitored_assets=[july_asset.key])
    def after_cursor_partitions_asset_sensor(context):
        events = context.latest_materialization_records_by_key([july_asset.key])

        if (
            events[july_asset.key]
            and events[july_asset.key].event_log_entry.dagster_event.partition == "2022-07-10"
        ):  # first sensor invocation
            context.advance_all_cursors()
        else:  # second sensor invocation
            assert context.get_cursor_partition(july_asset.key) == "2022-07-10"
            materializations_by_key = context.latest_materialization_records_by_key()
            later_materialization = materializations_by_key.get(july_asset.key)
            assert later_materialization
            assert later_materialization.event_log_entry.dagster_event.partition == "2022-07-05"

            materializations_by_partition = context.latest_materialization_records_by_partition(
                july_asset.key
            )
            assert list(materializations_by_partition.keys()) == ["2022-07-05"]

            materializations_by_partition = context.latest_materialization_records_by_partition(
                july_asset.key, after_cursor_partition=True
            )
            # The cursor is set to the 2022-07-10 partition. Future searches with the default
            # after_cursor_partition=True will only return materializations with partitions after
            # 2022-07-10.
            assert set(materializations_by_partition.keys()) == set()

    with dg.instance_for_test() as instance:
        dg.materialize(
            [july_asset],
            partition_key="2022-07-10",
            instance=instance,
        )
        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[july_asset.key], instance=instance, repository_def=my_repo
        )
        after_cursor_partitions_asset_sensor(ctx)
        dg.materialize([july_asset], partition_key="2022-07-05", instance=instance)
        after_cursor_partitions_asset_sensor(ctx)


def test_multi_asset_sensor_can_start_from_asset_sensor_cursor():
    @dg.asset
    def my_asset():
        return dg.Output(99)

    @dg.job
    def my_job():
        pass

    @asset_sensor(asset_key=my_asset.key, job=my_job)
    def my_asset_sensor(context):
        return dg.RunRequest(run_key=context.cursor, run_config={})

    @dg.multi_asset_sensor(monitored_assets=[my_asset.key])
    def my_multi_asset_sensor(context):
        ctx.advance_all_cursors()  # pyright: ignore[reportAttributeAccessIssue]

    with dg.instance_for_test() as instance:
        ctx = dg.build_sensor_context(
            instance=instance,
        )
        dg.materialize([my_asset], instance=instance)
        my_asset_sensor.evaluate_tick(ctx)

        assert ctx.cursor == "3"

        # simulate changing a @asset_sensor to a @multi_asset_sensor with the same name and
        # therefore inheriting the same cursor.
        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[my_asset.key],
            instance=instance,
            repository_def=my_repo,
            cursor=ctx.cursor,
        )
        my_multi_asset_sensor(ctx)

        assert ctx.cursor == "{\"AssetKey(['my_asset'])\": [null, 3, {}]}"


def test_multi_asset_sensor_all_partitions_materialized():
    @dg.multi_asset_sensor(monitored_assets=[july_asset.key])
    def asset_sensor(context):
        assert context.all_partitions_materialized(july_asset.key) is False
        assert (
            context.all_partitions_materialized(july_asset.key, ["2022-07-10", "2022-07-11"])
            is True
        )

    with dg.instance_for_test() as instance:
        dg.materialize(
            [july_asset],
            partition_key="2022-07-10",
            instance=instance,
        )
        dg.materialize(
            [july_asset],
            partition_key="2022-07-11",
            instance=instance,
        )
        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[july_asset.key], instance=instance, repository_def=my_repo
        )
        asset_sensor(ctx)


def test_multi_asset_sensor_partition_mapping():
    @dg.asset(partitions_def=dg.DailyPartitionsDefinition("2022-07-01"))
    def july_daily_partitions():
        return 1

    @dg.asset(
        partitions_def=dg.DailyPartitionsDefinition("2022-08-01"),
    )
    def downstream_daily_partitions(july_daily_partitions):
        return 1

    @dg.repository
    def my_repo():
        return [july_daily_partitions, downstream_daily_partitions]

    @dg.multi_asset_sensor(monitored_assets=[july_daily_partitions.key])
    def asset_sensor(context):
        for partition_key in context.latest_materialization_records_by_partition(
            july_daily_partitions.key
        ).keys():
            for downstream_partition in context.get_downstream_partition_keys(
                partition_key,
                to_asset_key=downstream_daily_partitions.key,
                from_asset_key=july_daily_partitions.key,
            ):
                assert downstream_partition == "2022-08-10"

    with dg.instance_for_test() as instance:
        dg.materialize(
            [july_daily_partitions],
            partition_key="2022-08-10",
            instance=instance,
        )
        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[july_daily_partitions.key],
            instance=instance,
            repository_def=my_repo,
        )
        asset_sensor(ctx)


def test_multi_asset_sensor_retains_ordering_and_fetches_latest_per_partition():
    partition_ordering = ["2022-07-15", "2022-07-14", "2022-07-13", "2022-07-12", "2022-07-15"]

    @dg.multi_asset_sensor(monitored_assets=[july_asset.key])
    def asset_sensor(context):
        assert (
            list(context.latest_materialization_records_by_partition(july_asset.key).keys())
            == partition_ordering[
                1:
            ]  # 2022-07-15 is duplicated, so we fetch the later materialization and ignore the first materialization
        )

    with dg.instance_for_test() as instance:
        for partition in partition_ordering:
            dg.materialize(
                [july_asset],
                partition_key=partition,
                instance=instance,
            )
        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[july_asset.key], instance=instance, repository_def=my_repo
        )
        asset_sensor(ctx)


def test_multi_asset_sensor_update_cursor_no_overwrite():
    @dg.multi_asset_sensor(monitored_assets=[july_asset.key, august_asset.key])
    def after_cursor_partitions_asset_sensor(context):
        events = context.latest_materialization_records_by_key()

        if (
            events[july_asset.key]
            and events[july_asset.key].event_log_entry.dagster_event.partition == "2022-07-10"
        ):  # first sensor invocation
            context.advance_cursor({july_asset.key: events[july_asset.key]})
        else:  # second sensor invocation
            materialization = events[august_asset.key]
            assert materialization
            context.advance_cursor({august_asset.key: materialization})

            assert (
                context._get_cursor(july_asset.key).latest_consumed_event_partition  # noqa: SLF001
                == "2022-07-10"
            )

    with dg.instance_for_test() as instance:
        dg.materialize(
            [july_asset],
            partition_key="2022-07-10",
            instance=instance,
        )
        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[july_asset.key, august_asset.key],
            instance=instance,
            repository_def=my_repo,
        )
        after_cursor_partitions_asset_sensor(ctx)
        dg.materialize([august_asset], partition_key="2022-08-05", instance=instance)
        after_cursor_partitions_asset_sensor(ctx)


def test_multi_asset_sensor_no_unconsumed_events():
    @dg.multi_asset_sensor(monitored_assets=[july_asset.key, july_asset_2.key])
    def my_sensor(context):
        # This call reads unconsumed event IDs from the cursor, fetches them from storage
        # and caches them in memory
        context.latest_materialization_records_by_partition_and_asset()
        # Assert that when no unconsumed events exist in the cursor, no events are cached
        assert context._initial_unconsumed_events_by_id == {}  # noqa: SLF001

    with dg.instance_for_test() as instance:
        dg.materialize([july_asset], partition_key="2022-08-04", instance=instance)
        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[july_asset.key, july_asset_2.key],
            instance=instance,
            repository_def=my_repo,
        )
        my_sensor(ctx)


def test_multi_asset_sensor_latest_materialization_records_by_partition_and_asset():
    @dg.multi_asset_sensor(monitored_assets=[july_asset.key, july_asset_2.key])
    def my_sensor(context):
        events = context.latest_materialization_records_by_partition_and_asset()
        for partition_key, materialization_by_asset in events.items():
            assert partition_key == "2022-08-04"
            assert len(materialization_by_asset) == 2
            assert july_asset.key in materialization_by_asset
            assert july_asset_2.key in materialization_by_asset

    with dg.instance_for_test() as instance:
        dg.materialize(
            [july_asset_2, july_asset],
            partition_key="2022-08-04",
            instance=instance,
        )
        dg.materialize([july_asset], partition_key="2022-08-04", instance=instance)
        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[july_asset.key, july_asset_2.key],
            instance=instance,
            repository_def=my_repo,
        )
        my_sensor(ctx)


def test_build_multi_asset_sensor_context_asset_selection():
    from dagster_tests.asset_defs_tests.test_asset_selection import (
        alice,
        bob,
        candace,
        danny,
        earth,
        edgar,
        fiona,
        george,
    )

    @dg.multi_asset_sensor(
        monitored_assets=AssetSelection.groups("ladies").upstream(depth=1, include_self=False)
    )
    def asset_selection_sensor(context):
        assert context.asset_keys == [danny.key]

    @dg.repository
    def my_repo():
        return [earth, alice, bob, candace, danny, edgar, fiona, george, asset_selection_sensor]

    with dg.instance_for_test() as instance:
        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=AssetSelection.groups("ladies").upstream(depth=1, include_self=False),
            instance=instance,
            repository_def=my_repo,
        )
        asset_selection_sensor(ctx)


def test_multi_asset_sensor_unconsumed_events():
    invocation_num = 0

    @dg.multi_asset_sensor(monitored_assets=[july_asset.key])
    def test_unconsumed_events_sensor(context):
        if invocation_num == 0:
            events = context.latest_materialization_records_by_partition(july_asset.key)
            assert len(events) == 2
            context.advance_cursor(
                {july_asset.key: events["2022-07-10"]}
            )  # advance to later materialization
        if invocation_num == 1:
            # Should fetch unconsumed 2022-07-05 event
            events = context.latest_materialization_records_by_partition(july_asset.key)
            assert len(events) == 1
            context.advance_cursor({july_asset.key: events["2022-07-05"]})

    with dg.instance_for_test() as instance:
        # Invocation 0:
        # Materialize partition 2022-07-05. Then materialize 2022-07-10 twice, updating cursor
        # to the later 2022-07-10 materialization. The first 2022-07-05 materialization should be unconsumed.
        dg.materialize(
            [july_asset],
            partition_key="2022-07-05",
            instance=instance,
        )
        dg.materialize([july_asset], partition_key="2022-07-10", instance=instance)
        dg.materialize([july_asset], partition_key="2022-07-10", instance=instance)

        event_records = list(
            instance.fetch_materializations(july_asset.key, ascending=True, limit=5000).records
        )
        assert len(event_records) == 3
        first_2022_07_10_mat = event_records[1].storage_id
        unconsumed_storage_id = event_records[0].storage_id
        assert first_2022_07_10_mat > unconsumed_storage_id
        assert first_2022_07_10_mat < event_records[2].storage_id

        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[july_asset.key], instance=instance, repository_def=my_repo
        )
        test_unconsumed_events_sensor(ctx)
        july_asset_cursor = ctx._get_cursor(july_asset.key)  # noqa: SLF001
        assert first_2022_07_10_mat < july_asset_cursor.latest_consumed_event_id  # pyright: ignore[reportOperatorIssue]
        assert july_asset_cursor.latest_consumed_event_partition == "2022-07-10"
        # Second materialization for 2022-07-10 is after cursor so should not be unconsumed
        assert july_asset_cursor.trailing_unconsumed_partitioned_event_ids == {
            "2022-07-05": unconsumed_storage_id
        }

        # Invocation 1:
        # Confirm that the unconsumed event is fetched. After, the unconsumed event should
        # no longer show up in the cursor. The storage ID of the cursor should stay the same.
        invocation_num += 1
        test_unconsumed_events_sensor(ctx)
        second_july_cursor = ctx._get_cursor(july_asset.key)  # noqa: SLF001
        assert second_july_cursor.latest_consumed_event_partition == "2022-07-10"
        assert (
            second_july_cursor.latest_consumed_event_id
            == july_asset_cursor.latest_consumed_event_id
        )
        assert second_july_cursor.trailing_unconsumed_partitioned_event_ids == {}


def test_advance_all_cursors_clears_unconsumed_events():
    invocation_num = 0

    @dg.multi_asset_sensor(monitored_assets=[july_asset.key])
    def test_unconsumed_events_sensor(context):
        if invocation_num == 0:
            events = context.latest_materialization_records_by_partition(july_asset.key)
            assert len(events) == 2
            context.advance_cursor(
                {july_asset.key: events["2022-07-10"]}
            )  # advance to later materialization
        if invocation_num == 1:
            # Should fetch unconsumed event
            events = context.latest_materialization_records_by_partition(july_asset.key)
            assert len(events) == 2
            unconsumed_events = context.get_trailing_unconsumed_events(july_asset.key)
            assert len(unconsumed_events) == 1
            assert events["2022-07-05"] == unconsumed_events[0]
            context.advance_all_cursors()

    with dg.instance_for_test() as instance:
        # Invocation 0:
        # Materialize partition 2022-07-05. Then materialize 2022-07-10, updating cursor
        # to the 2022-07-10 materialization. The first 2022-07-05 materialization should be unconsumed.
        dg.materialize(
            [july_asset],
            partition_key="2022-07-05",
            instance=instance,
        )
        dg.materialize([july_asset], partition_key="2022-07-10", instance=instance)

        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[july_asset.key], instance=instance, repository_def=my_repo
        )
        test_unconsumed_events_sensor(ctx)
        july_asset_cursor = ctx._get_cursor(july_asset.key)  # noqa: SLF001
        first_storage_id = july_asset_cursor.latest_consumed_event_id
        assert first_storage_id
        assert july_asset_cursor.latest_consumed_event_partition == "2022-07-10"
        assert len(july_asset_cursor.trailing_unconsumed_partitioned_event_ids) == 1

        # Invocation 1:
        # Confirm that the unconsumed event is fetched. After calling advance_all_cursors,
        # all unconsumed events should be cleared. The storage ID of the cursor should stay the same.
        invocation_num += 1
        dg.materialize(
            [july_asset],
            partition_key="2022-07-06",
            instance=instance,
        )
        test_unconsumed_events_sensor(ctx)
        july_asset_cursor = ctx._get_cursor(july_asset.key)  # noqa: SLF001
        assert july_asset_cursor.latest_consumed_event_partition == "2022-07-06"
        assert july_asset_cursor.trailing_unconsumed_partitioned_event_ids == {}
        assert july_asset_cursor.latest_consumed_event_id > first_storage_id  # pyright: ignore[reportOptionalOperand]


def test_error_when_max_num_unconsumed_events():
    @dg.multi_asset_sensor(monitored_assets=[july_asset.key])
    def test_unconsumed_events_sensor(context):
        latest_record = context.materialization_records_for_key(july_asset.key, limit=25)
        context.advance_cursor({july_asset.key: latest_record[-1]})

    with dg.instance_for_test() as instance:
        # Invocation 0:
        # Materialize partition 2022-07-05. Then materialize 2022-07-10, updating cursor
        # to the 2022-07-10 materialization. The first 2022-07-05 materialization should be unconsumed.
        for num in range(1, 26):
            str_num = "0" + str(num) if num < 10 else str(num)
            dg.materialize(
                [july_asset],
                partition_key=f"2022-07-{str_num}",
                instance=instance,
            )
        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[july_asset.key], instance=instance, repository_def=my_repo
        )
        test_unconsumed_events_sensor(ctx)
        july_asset_cursor = ctx._get_cursor(july_asset.key)  # noqa: SLF001
        assert july_asset_cursor.latest_consumed_event_id
        assert july_asset_cursor.latest_consumed_event_partition == "2022-07-25"
        assert len(july_asset_cursor.trailing_unconsumed_partitioned_event_ids) == 24

        for date in ["26", "27", "28"]:
            dg.materialize(
                [july_asset],
                partition_key=f"2022-07-{date}",
                instance=instance,
            )
        with pytest.raises(
            dg.DagsterInvariantViolationError,
            match="maximum number of trailing unconsumed events",
        ):
            test_unconsumed_events_sensor(ctx)


def test_latest_materialization_records_by_partition_fetches_unconsumed_events():
    invocation_num = 0

    @dg.multi_asset_sensor(monitored_assets=[july_asset.key])
    def test_unconsumed_events_sensor(context):
        if invocation_num == 0:
            context.advance_cursor(
                {
                    july_asset.key: context.latest_materialization_records_by_partition(
                        july_asset.key
                    )["2022-07-03"]
                }
            )
        if invocation_num == 1:
            # At this point, partitions 01, 02 are unconsumed and 04 is the latest materialization.
            # Because we return the latest materialization per partition in order of storage ID,
            # we expect to see materializations 01, 04, and 02 in that order.
            records_dict = context.latest_materialization_records_by_partition(july_asset.key)

            ordered_records = list(enumerate(records_dict))
            get_partition_key_from_ordered_record = lambda record: record[1]
            assert [
                get_partition_key_from_ordered_record(record) for record in ordered_records
            ] == ["2022-07-01", "2022-07-04", "2022-07-02"]

            for event_log_entry in records_dict.values():
                context.advance_cursor({july_asset.key: event_log_entry})

    with dg.instance_for_test() as instance:
        # Invocation 0:
        # Materialize partition 01, 02, and 03, advancing the cursor to 03. 01 and 02 are unconsumed events.
        for date in ["01", "02", "03"]:
            dg.materialize(
                [july_asset],
                partition_key=f"2022-07-{date}",
                instance=instance,
            )
        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[july_asset.key], instance=instance, repository_def=my_repo
        )
        test_unconsumed_events_sensor(ctx)
        first_july_cursor = ctx._get_cursor(july_asset.key)  # noqa: SLF001
        assert first_july_cursor.latest_consumed_event_id
        assert first_july_cursor.latest_consumed_event_partition == "2022-07-03"
        assert len(first_july_cursor.trailing_unconsumed_partitioned_event_ids) == 2

        invocation_num += 1
        for date in ["04", "02"]:
            dg.materialize(
                [july_asset],
                partition_key=f"2022-07-{date}",
                instance=instance,
            )
        test_unconsumed_events_sensor(ctx)
        second_july_cursor = ctx._get_cursor(july_asset.key)  # noqa: SLF001
        assert second_july_cursor.latest_consumed_event_partition == "2022-07-02"
        assert (
            second_july_cursor.latest_consumed_event_id > first_july_cursor.latest_consumed_event_id  # pyright: ignore[reportOptionalOperand]
        )
        # We should remove the 2022-07-02 materialization from the unconsumed events list
        # since we have advanced the cursor for a later materialization with that partition key.
        assert len(second_july_cursor.trailing_unconsumed_partitioned_event_ids.keys()) == 0


def test_unfetched_partitioned_events_are_unconsumed():
    @dg.multi_asset_sensor(monitored_assets=[july_asset.key])
    def test_unconsumed_events_sensor(context):
        context.advance_cursor(
            {
                july_asset.key: context.latest_materialization_records_by_partition(july_asset.key)[
                    "2022-07-05"
                ]
            }
        )

    with dg.instance_for_test() as instance:
        for _ in range(5):
            dg.materialize(
                [july_asset],
                partition_key="2022-07-04",
                instance=instance,
            )
            dg.materialize(
                [july_asset],
                partition_key="2022-07-05",
                instance=instance,
            )
        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[july_asset.key], instance=instance, repository_def=my_repo
        )
        test_unconsumed_events_sensor(ctx)
        first_july_cursor = ctx._get_cursor(july_asset.key)  # noqa: SLF001
        assert first_july_cursor.latest_consumed_event_id
        assert first_july_cursor.latest_consumed_event_partition == "2022-07-05"

        mats_2022_07_04 = list(
            instance.fetch_materializations(
                records_filter=dg.AssetRecordsFilter(
                    asset_key=july_asset.key, asset_partitions=["2022-07-04"]
                ),
                limit=1,
            ).records
        )
        # Assert that the unconsumed event points to the most recent 2022_07_04 materialization.
        assert (
            first_july_cursor.trailing_unconsumed_partitioned_event_ids["2022-07-04"]
            == mats_2022_07_04[0].storage_id
        )

        dg.materialize(
            [july_asset],
            partition_key="2022-07-04",
            instance=instance,
        )
        dg.materialize(
            [july_asset],
            partition_key="2022-07-05",
            instance=instance,
        )

        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[july_asset.key], instance=instance, repository_def=my_repo
        )
        test_unconsumed_events_sensor(ctx)
        second_july_cursor = ctx._get_cursor(july_asset.key)  # noqa: SLF001
        assert (
            second_july_cursor.latest_consumed_event_id > first_july_cursor.latest_consumed_event_id  # pyright: ignore[reportOptionalOperand]
        )
        assert second_july_cursor.latest_consumed_event_partition == "2022-07-05"
        assert (
            second_july_cursor.trailing_unconsumed_partitioned_event_ids["2022-07-04"]
            > first_july_cursor.trailing_unconsumed_partitioned_event_ids["2022-07-04"]
        )


def test_build_multi_asset_sensor_context_asset_selection_set_to_latest_materializations():
    @dg.asset
    def my_asset():
        pass

    @dg.multi_asset_sensor(monitored_assets=[my_asset.key])
    def my_sensor(context):
        my_asset_cursor = context._get_cursor(my_asset.key)  # noqa: SLF001
        assert my_asset_cursor.latest_consumed_event_id is not None

    @dg.repository
    def my_repo():
        return [my_asset, my_sensor]

    with dg.instance_for_test() as instance:
        result = dg.materialize([my_asset], instance=instance)
        record = next(iter(instance.fetch_materializations(my_asset.key, limit=1).records))
        assert record.event_log_entry.run_id == result.run_id

        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=AssetSelection.groups("default"),
            instance=instance,
            cursor_from_latest_materializations=True,
            repository_def=my_repo,
        )
        assert (
            ctx._get_cursor(my_asset.key).latest_consumed_event_id  # noqa: SLF001
            == record.storage_id
        )
        my_sensor(ctx)


def test_build_multi_asset_sensor_context_set_to_latest_materializations():
    evaluated = False

    @dg.asset
    def my_asset():
        return dg.Output(1, metadata={"evaluated": evaluated})

    @dg.multi_asset_sensor(monitored_assets=[my_asset.key])
    def my_sensor(context):
        if not evaluated:
            assert context.latest_materialization_records_by_key()[my_asset.key] is None
        else:
            # Test that materialization exists
            assert context.latest_materialization_records_by_key()[
                my_asset.key
            ].event_log_entry.dagster_event.materialization.metadata[
                "evaluated"
            ] == MetadataValue.bool(True)

    @dg.repository
    def my_repo():
        return [my_asset, my_sensor]

    with dg.instance_for_test() as instance:
        result = dg.materialize([my_asset], instance=instance)
        record = next(iter(instance.fetch_materializations(my_asset.key, limit=1).records))
        assert record.event_log_entry.run_id == result.run_id

        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[my_asset.key],
            instance=instance,
            cursor_from_latest_materializations=True,
            repository_def=my_repo,
        )
        assert (
            ctx._get_cursor(my_asset.key).latest_consumed_event_id  # noqa: SLF001
            == record.storage_id
        )
        my_sensor(ctx)
        evaluated = True

        dg.materialize([my_asset], instance=instance)
        my_sensor(ctx)


def test_build_multi_asset_context_set_after_multiple_materializations():
    @dg.asset
    def my_asset():
        return 1

    @dg.asset
    def my_asset_2():
        return 1

    @dg.repository
    def my_repo():
        return [my_asset, my_asset_2]

    with dg.instance_for_test() as instance:
        dg.materialize([my_asset], instance=instance)
        dg.materialize([my_asset_2], instance=instance)

        my_asset_record = next(iter(instance.fetch_materializations(my_asset.key, limit=1).records))
        my_asset_2_record = next(
            iter(instance.fetch_materializations(my_asset_2.key, limit=1).records)
        )

        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[my_asset.key, my_asset_2.key],
            instance=instance,
            cursor_from_latest_materializations=True,
            repository_def=my_repo,
        )
        assert (
            ctx._get_cursor(my_asset.key).latest_consumed_event_id  # noqa: SLF001
            == my_asset_record.storage_id
        )
        assert (
            ctx._get_cursor(my_asset_2.key).latest_consumed_event_id  # noqa: SLF001
            == my_asset_2_record.storage_id
        )


def test_error_exec_in_process_to_build_multi_asset_sensor_context():
    @dg.asset
    def my_asset():
        return 1

    @dg.repository
    def my_repo():
        return [my_asset]

    with pytest.raises(dg.DagsterInvalidInvocationError, match="Dagster instance"):
        with dg.instance_for_test() as instance:
            dg.materialize([my_asset], instance=instance)
            dg.build_multi_asset_sensor_context(
                monitored_assets=[my_asset.key],
                repository_def=my_repo,
                cursor_from_latest_materializations=True,
            )

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match="Cannot provide both cursor and cursor_from_latest_materializations",
    ):
        with dg.instance_for_test() as instance:
            dg.materialize([my_asset], instance=instance)
            dg.build_multi_asset_sensor_context(
                monitored_assets=[my_asset.key],
                repository_def=my_repo,
                cursor_from_latest_materializations=True,
                cursor="alskdjalsjk",
            )


def test_error_not_thrown_for_skip_reason():
    @dg.multi_asset_sensor(monitored_assets=[july_asset.key])
    def test_unconsumed_events_sensor(_):
        return dg.SkipReason("I am skipping")

    with dg.instance_for_test() as instance:
        ctx = dg.build_multi_asset_sensor_context(
            monitored_assets=[july_asset.key],
            repository_def=my_repo,
            instance=instance,
        )
        test_unconsumed_events_sensor(ctx)


def test_dynamic_partitions_sensor():
    dynamic_partitions_def = dg.DynamicPartitionsDefinition(name="fruits")

    @dg.asset(partitions_def=dynamic_partitions_def)
    def fruits_asset():
        return 1

    my_job = dg.define_asset_job(
        "fruits_job", [fruits_asset], partitions_def=dynamic_partitions_def
    )

    @dg.repository
    def my_repo():
        return [fruits_asset]

    @dg.sensor(job=my_job)
    def test_sensor(context):
        context.instance.add_dynamic_partitions(dynamic_partitions_def.name, ["apple"])
        return dg.RunRequest(partition_key="apple")

    with dg.instance_for_test() as instance:
        ctx = dg.build_sensor_context(
            repository_def=my_repo,
            instance=instance,
        )
        run_request = test_sensor(ctx)
        assert run_request.partition_key == "apple"  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]


def test_sensor_invocation_runconfig() -> None:
    class MyConfig(dg.Config):
        a_str: str
        an_int: int

    # Test no arg invocation
    @dg.sensor(job_name="foo_job")
    def basic_sensor():
        return dg.RunRequest(
            run_key=None,
            run_config=dg.RunConfig(ops={"foo": MyConfig(a_str="foo", an_int=55)}),
            tags={},
        )

    assert cast("dg.RunRequest", basic_sensor()).run_config.get("ops", {}) == {
        "foo": {"config": {"a_str": "foo", "an_int": 55}}
    }


def test_empty_asset_selection():
    @dg.asset
    def asset1():
        pass

    @dg.sensor(asset_selection=AssetSelection.all())
    def my_sensor(context):
        return dg.RunRequest(asset_selection=[])

    @dg.repository
    def my_repo():
        return [asset1, my_sensor]

    with dg.instance_for_test() as instance:
        ctx = dg.build_sensor_context(
            repository_def=my_repo,
            instance=instance,
        )
        exec_data = my_sensor.evaluate_tick(ctx)
        assert exec_data.run_requests[0].asset_selection == []  # pyright: ignore[reportOptionalSubscript]


def test_reject_invalid_asset_check_keys():
    @dg.asset
    def asset1():
        pass

    @dg.asset
    def asset2():
        pass

    @dg.asset_check(asset=asset1)
    def check1():
        return dg.AssetCheckResult(passed=True)

    @dg.sensor(asset_selection=AssetSelection.assets(asset1))
    def asset1_sensor(context):
        return dg.RunRequest(asset_check_keys=[check1.check_key])

    @dg.sensor(asset_selection=AssetSelection.assets(asset2))
    def asset2_sensor(context):
        return dg.RunRequest(asset_check_keys=[check1.check_key])

    my_repo = dg.Definitions(
        assets=[asset1, asset2],
        asset_checks=[check1],
        sensors=[asset1_sensor, asset2_sensor],
    ).get_repository_def()

    with dg.instance_for_test() as instance:
        ctx = dg.build_sensor_context(
            repository_def=my_repo,
            instance=instance,
        )
        asset1_sensor_data = asset1_sensor.evaluate_tick(ctx)
        assert asset1_sensor_data.run_requests[0].asset_selection == [asset1.key]  # pyright: ignore[reportOptionalSubscript]
        assert asset1_sensor_data.run_requests[0].asset_check_keys == [check1.check_key]  # pyright: ignore[reportOptionalSubscript]

        with pytest.warns(DeprecationWarning, match="asset check keys"):
            asset2_sensor.evaluate_tick(ctx)


def test_run_status_sensor_eval_tick_testing() -> None:
    # Ensure run status senors can be tested including exercising the logic
    # provided by us. Useful for ensuring its been defined correctly.

    @dg.job
    def certain_job(): ...

    @dg.job
    def other_job(): ...

    @dg.job
    def job_1(): ...

    @dg.job
    def job_2(): ...

    @dg.job
    def job_3(): ...

    @dg.run_status_sensor(
        monitored_jobs=[certain_job],
        request_job=job_1,
        run_status=DagsterRunStatus.SUCCESS,
    )
    def sensor_1():
        return dg.RunRequest(
            job_name="job_1",
        )

    @dg.run_status_sensor(
        monitored_jobs=[certain_job],
        request_job=job_2,
        run_status=DagsterRunStatus.SUCCESS,
    )
    def sensor_2():
        return dg.RunRequest(
            job_name="job_2",
        )

    @dg.run_status_sensor(
        monitored_jobs=[other_job],
        request_job=job_3,
        run_status=DagsterRunStatus.SUCCESS,
    )
    def sensor_3():
        return dg.RunRequest(
            job_name="job_3",
        )

    instance = DagsterInstance.ephemeral()

    sensors = [sensor_1, sensor_2, sensor_3]
    cursors = {}

    result = job_1.execute_in_process(instance=instance)
    assert result.success

    # the first run of a status sensor starts tracking from that point,
    # so run each one and save the cursor
    for s in sensors:
        ctx = dg.build_sensor_context(instance=instance)
        data = s.evaluate_tick(ctx)
        cursors[s] = data.cursor

    # execute the target job
    result = certain_job.execute_in_process(instance=instance)
    assert result.success

    # evaluate all sensors
    requested_jobs = set()
    for s in sensors:
        ctx = dg.build_sensor_context(
            instance=instance,
            cursor=cursors[s],
        )
        data = s.evaluate_tick(ctx)
        for request in data.run_requests or []:
            requested_jobs.add(request.job_name)

    # assert the expected response amongst sensors
    assert requested_jobs == {"job_1", "job_2"}
