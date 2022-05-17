import pytest

from dagster import (
    DagsterInvalidDefinitionError,
    JobDefinition,
    ResourceDefinition,
    graph,
    io_manager,
    job,
    mem_io_manager,
    op,
    schedule,
    sensor,
)
from dagster.core.asset_defs import AssetsDefinition, asset, build_assets_job
from dagster.core.definitions.pending_job_definition import (
    PendingJobDefinition,  # type: ignore[attr-defined]
)
from dagster.core.execution.with_resources import with_resources
from dagster.core.storage.mem_io_manager import InMemoryIOManager

# pylint: disable=comparison-with-callable


def test_graph():
    @op(required_resource_keys={"foo", "bar"})
    def the_op():
        pass

    @graph
    def the_graph():
        the_op()

    the_pending_job = with_resources(
        [the_graph], {"foo": ResourceDefinition.hardcoded_resource("blah")}
    )[0]
    assert isinstance(the_pending_job, PendingJobDefinition)
    the_full_job = with_resources(
        [the_graph],
        {
            "foo": ResourceDefinition.hardcoded_resource("blah"),
            "bar": ResourceDefinition.hardcoded_resource("blah"),
        },
    )[0]
    assert isinstance(the_full_job, JobDefinition)
    assert the_full_job.execute_in_process().success


def test_pending_job():
    @op(required_resource_keys={"foo", "bar"})
    def the_op():
        pass

    @graph
    def the_graph():
        the_op()

    orig_foo = ResourceDefinition.hardcoded_resource("blah")

    the_pending_job = with_resources([the_graph], {"foo": orig_foo})[0]
    the_full_job = with_resources(
        [the_pending_job],
        {
            "foo": ResourceDefinition.hardcoded_resource("blah"),
            "bar": ResourceDefinition.hardcoded_resource("blah"),
        },
    )[0]
    assert isinstance(the_full_job, JobDefinition)
    assert the_full_job.resource_defs["foo"] == orig_foo
    assert the_full_job.execute_in_process().success


def test_job_definition():
    @op(required_resource_keys={"foo"})
    def the_op():
        pass

    orig_foo = ResourceDefinition.hardcoded_resource("blah")

    @job(resource_defs={"foo": orig_foo})
    def the_job():
        the_op()

    updated_job = with_resources(
        [the_job],
        {"io_manager": mem_io_manager, "foo": ResourceDefinition.hardcoded_resource("blah")},
    )[0]
    assert isinstance(updated_job, JobDefinition)
    assert updated_job.resource_defs["io_manager"] == mem_io_manager
    assert updated_job.resource_defs["foo"] == orig_foo


def test_schedule_targets_graph():
    @op(required_resource_keys={"foo"})
    def the_op(context):
        assert context.resources.foo == "blah"

    @graph
    def the_graph():
        the_op()

    @schedule(cron_schedule="* * * * *", job=the_graph)
    def the_schedule():
        pass

    transformed_schedule = with_resources(
        [the_schedule], {"foo": ResourceDefinition.hardcoded_resource("blah")}
    )[0]
    the_job = transformed_schedule.job
    assert isinstance(the_job, JobDefinition)
    assert the_job.execute_in_process().success


def test_schedule_targets_pending_job():
    @op(required_resource_keys={"foo", "bar"})
    def the_op():
        pass

    @graph
    def the_graph():
        the_op()

    orig_foo = ResourceDefinition.hardcoded_resource("blah")

    the_pending_job = with_resources([the_graph], {"foo": orig_foo})[0]
    assert isinstance(the_pending_job, PendingJobDefinition)

    @schedule(cron_schedule="* * * * *", job=the_pending_job)
    def the_schedule():
        pass

    transformed_schedule = with_resources(
        [the_schedule], {"bar": ResourceDefinition.hardcoded_resource("blah")}
    )[0]
    assert isinstance(transformed_schedule.job, JobDefinition)

    assert transformed_schedule.job.execute_in_process().success


def test_schedule_targets_job():
    @op(required_resource_keys={"foo"})
    def the_op():
        pass

    orig_foo = ResourceDefinition.hardcoded_resource("blah")

    @job(resource_defs={"foo": orig_foo})
    def the_job():
        the_op()

    @schedule(cron_schedule="* * * * *", job=the_job)
    def the_schedule():
        pass

    transformed_schedule = with_resources(
        [the_schedule],
        {"foo": ResourceDefinition.hardcoded_resource("blah")},
    )[0]
    assert transformed_schedule.job == the_job

    transformed_schedule = with_resources(
        [the_schedule],
        {"io_manager": mem_io_manager},
    )[0]

    assert isinstance(transformed_schedule.job, JobDefinition)
    assert transformed_schedule.job.resource_defs["io_manager"] == mem_io_manager


def test_sensor_targets_graph():
    @op(required_resource_keys={"foo"})
    def the_op(context):
        assert context.resources.foo == "blah"

    @graph
    def the_graph():
        the_op()

    @sensor(job=the_graph)
    def the_sensor():
        pass

    transformed_sensor = with_resources(
        [the_sensor], {"foo": ResourceDefinition.hardcoded_resource("blah")}
    )[0]
    the_job = transformed_sensor.job
    assert isinstance(the_job, JobDefinition)
    assert the_job.execute_in_process().success


def test_sensor_targets_pending_job():
    @op(required_resource_keys={"foo", "bar"})
    def the_op():
        pass

    @graph
    def the_graph():
        the_op()

    orig_foo = ResourceDefinition.hardcoded_resource("blah")

    the_pending_job = with_resources([the_graph], {"foo": orig_foo})[0]
    assert isinstance(the_pending_job, PendingJobDefinition)

    @sensor(job=the_pending_job)
    def the_sensor():
        pass

    transformed_sensor = with_resources(
        [the_sensor], {"bar": ResourceDefinition.hardcoded_resource("blah")}
    )[0]
    assert isinstance(transformed_sensor.job, JobDefinition)

    assert transformed_sensor.job.execute_in_process().success


def test_sensor_targets_job():
    @op(required_resource_keys={"foo"})
    def the_op():
        pass

    orig_foo = ResourceDefinition.hardcoded_resource("blah")

    @job(resource_defs={"foo": orig_foo})
    def the_job():
        the_op()

    @sensor(job=the_job)
    def the_sensor():
        pass

    transformed_sensor = with_resources(
        [the_sensor],
        {"foo": ResourceDefinition.hardcoded_resource("blah")},
    )[0]
    assert transformed_sensor.job == the_job

    transformed_sensor = with_resources(
        [the_sensor],
        {"io_manager": mem_io_manager},
    )[0]

    assert isinstance(transformed_sensor.job, JobDefinition)
    assert transformed_sensor.job.resource_defs["io_manager"] == mem_io_manager


def test_assets_direct():
    @asset(required_resource_keys={"foo"})
    def the_asset(context):
        assert context.resources.foo == "blah"
        return 5

    in_mem = InMemoryIOManager()

    @io_manager
    def the_io_manager():
        return in_mem

    transformed_asset = with_resources(
        [the_asset],
        {"foo": ResourceDefinition.hardcoded_resource("blah"), "io_manager": the_io_manager},
    )[0]
    assert isinstance(transformed_asset, AssetsDefinition)

    assert build_assets_job("the_job", [transformed_asset]).execute_in_process().success
    assert list(in_mem.values.values())[0] == 5


def test_assets_direct_resource_conflicts():
    @asset(required_resource_keys={"foo"})
    def the_asset():
        pass

    @asset(required_resource_keys={"foo"})
    def other_asset():
        pass

    transformed_asset = with_resources(
        [the_asset],
        {"foo": ResourceDefinition.hardcoded_resource("blah")},
    )[0]

    other_transformed_asset = with_resources(
        [other_asset],
        {"foo": ResourceDefinition.hardcoded_resource("blah")},
    )[0]

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="had a conflicting version of the same resource key foo. Please resolve this conflict by giving different keys to each resource definition.",
    ):
        build_assets_job("the_job", [transformed_asset, other_transformed_asset])
