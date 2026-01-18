import warnings
from datetime import datetime

import dagster as dg
import pytest
from dagster._core.definitions.metadata.metadata_value import MetadataValue
from dagster._core.definitions.partitions.partitioned_schedule import (
    UnresolvedPartitionedAssetScheduleDefinition,
)


def test_default_name():
    schedule = dg.ScheduleDefinition(job_name="my_pipeline", cron_schedule="0 0 * * *")
    assert schedule.name == "my_pipeline_schedule"


def test_default_name_graph():
    @dg.graph
    def my_graph():
        pass

    schedule = dg.ScheduleDefinition(job=my_graph, cron_schedule="0 0 * * *")
    assert schedule.name == "my_graph_schedule"


def test_default_name_job():
    @dg.graph
    def my_graph():
        pass

    schedule = dg.ScheduleDefinition(job=my_graph.to_job(name="my_job"), cron_schedule="0 0 * * *")
    assert schedule.name == "my_job_schedule"


def test_jobs_attr():
    @dg.graph
    def my_graph():
        pass

    schedule = dg.ScheduleDefinition(job=my_graph, cron_schedule="0 0 * * *")
    assert schedule.job.name == my_graph.name

    schedule = dg.ScheduleDefinition(job_name="my_pipeline", cron_schedule="0 0 * * *")
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="No job was provided to ScheduleDefinition.",
    ):
        schedule.job  # noqa: B018


def test_invalid_cron_schedule():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="invalid cron schedule",
    ):
        schedule = dg.ScheduleDefinition(job_name="my_pipeline", cron_schedule="oopsies * * * *")
        assert schedule.name == "my_pipeline_schedule"


def test_weird_cron_inteval():
    with pytest.warns(
        UserWarning,
        match="cron schedule with an interval greater than the expected range",
    ):
        schedule = dg.ScheduleDefinition(job_name="my_pipeline", cron_schedule="*/90 * * * *")
        assert schedule.name == "my_pipeline_schedule"


def test_invalid_tag_keys():
    # turn off any outer warnings filters, e.g. ignores that are set in pyproject.toml
    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as caught_warnings:
        dg.ScheduleDefinition(
            job_name="my_pipeline",
            cron_schedule="0 0 * * *",
            tags={"my_tag&": "yes", "my_tag#": "yes"},
        )

        assert len(caught_warnings) == 1
        warning = caught_warnings[0]
        assert "Non-compliant tag keys like ['my_tag&', 'my_tag#'] are deprecated" in str(
            warning.message
        )
        assert warning.filename.endswith("test_schedule.py")


def test_schedule_run_config_obj() -> None:
    my_schedule = dg.ScheduleDefinition(
        name="my_schedule",
        cron_schedule="* * * * *",
        job_name="test_job",
        run_config=dg.RunConfig(ops={"foo": "bar"}),
    )

    execution_time = datetime(year=2019, month=2, day=27)
    context_with_time = dg.build_schedule_context(scheduled_execution_time=execution_time)

    execution_data = my_schedule.evaluate_tick(context_with_time)
    assert execution_data.run_requests
    assert len(execution_data.run_requests) == 1
    assert execution_data.run_requests[0].run_config["ops"] == {"foo": "bar"}


def test_schedule_run_config_obj_fn() -> None:
    my_schedule = dg.ScheduleDefinition(
        name="my_schedule",
        cron_schedule="* * * * *",
        job_name="test_job",
        run_config_fn=lambda ctx: dg.RunConfig(
            ops={"baz": "qux", "time": ctx.scheduled_execution_time}
        ),
    )

    execution_time = datetime(year=2019, month=2, day=27)
    context_with_time = dg.build_schedule_context(scheduled_execution_time=execution_time)

    execution_data = my_schedule.evaluate_tick(context_with_time)
    assert execution_data.run_requests
    assert len(execution_data.run_requests) == 1
    assert execution_data.run_requests[0].run_config["ops"] == {
        "baz": "qux",
        "time": execution_time,
    }


def test_coerce_graph_def_to_job():
    @dg.op
    def foo(): ...

    @dg.graph
    def bar():
        foo()

    with pytest.warns(DeprecationWarning, match="Passing GraphDefinition"):
        my_schedule = dg.ScheduleDefinition(cron_schedule="* * * * *", job=bar)

    assert isinstance(my_schedule.job, dg.JobDefinition)
    assert my_schedule.job.name == "bar"


def test_tag_transfer_to_run_request():
    tags_and_exec_fn_schedule = dg.ScheduleDefinition(
        cron_schedule="@daily",
        job_name="the_job",
        tags={"foo": "bar"},
        execution_fn=lambda _: dg.RunRequest(),
    )

    tags_and_no_exec_fn_schedule = dg.ScheduleDefinition(
        cron_schedule="@daily",
        job_name="the_job",
        tags={"foo": "bar"},
    )

    execution_time = datetime(year=2019, month=2, day=27)
    context_with_time = dg.build_schedule_context(scheduled_execution_time=execution_time)

    # If no defined execution function, tags should be transferred to the run request (backcompat)
    assert (
        tags_and_no_exec_fn_schedule.evaluate_tick(context_with_time).run_requests[0].tags["foo"]  # pyright: ignore[reportOptionalSubscript]
        == "bar"
    )

    # If an execution function is defined, tags should not be transferred to the run request
    assert (
        "foo" not in tags_and_exec_fn_schedule.evaluate_tick(context_with_time).run_requests[0].tags  # pyright: ignore[reportOptionalSubscript]
    )


def test_with_updated_job():
    @dg.op
    def my_op():
        pass

    @dg.job
    def my_job_1():
        my_op()

    @dg.job
    def my_job_2():
        my_op()

    my_schedule_1 = dg.ScheduleDefinition(
        job=my_job_1, cron_schedule="@daily", tags={"foo": "bar"}, metadata={"baz": "qux"}
    )

    my_schedule_2 = my_schedule_1.with_updated_job(my_job_2)

    assert my_schedule_2.job.name == "my_job_2"
    assert my_schedule_2.cron_schedule == "@daily"
    assert my_schedule_2.tags == {"foo": "bar"}
    assert my_schedule_2.metadata == {"baz": MetadataValue.text("qux")}


def test_with_updated_metadata():
    schedule = dg.ScheduleDefinition(
        job_name="job", cron_schedule="@daily", metadata={"baz": "qux"}
    )
    assert schedule.metadata == {"baz": MetadataValue.text("qux")}

    blanked = schedule.with_attributes(metadata={})
    assert blanked.metadata == {}

    @dg.job
    def my_job(): ...

    schedule = dg.ScheduleDefinition(job=my_job, cron_schedule="@daily", metadata={"foo": "bar"})
    updated = schedule.with_attributes(metadata={**schedule.metadata, "foo": "baz"})
    assert updated.metadata["foo"] == dg.TextMetadataValue("baz")


def test_unresolved_metadata():
    @dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2020-01-01"))
    def asset1(): ...

    asset1_job = dg.define_asset_job("asset1_job", selection=[asset1])
    unresolved_schedule = dg.build_schedule_from_partitioned_job(
        asset1_job, name="my_schedule", metadata={"foo": "bar", "four": 4}
    )
    assert isinstance(unresolved_schedule, UnresolvedPartitionedAssetScheduleDefinition)
    assert unresolved_schedule.metadata
    assert unresolved_schedule.metadata["foo"] == "bar"

    blanked = unresolved_schedule.with_metadata({})
    assert blanked.metadata == {}

    updated = unresolved_schedule.with_metadata({**unresolved_schedule.metadata, "foo": "baz"})
    assert updated.metadata
    assert updated.metadata["foo"] == "baz"
    assert updated.metadata["four"] == 4

    defs = dg.Definitions(
        schedules=[updated],
        jobs=[asset1_job],
        assets=[asset1],
    )

    schedule = defs.resolve_schedule_def("my_schedule")
    assert schedule.metadata["foo"] == dg.TextMetadataValue("baz")
    assert schedule.metadata["four"] == dg.IntMetadataValue(4)


def test_owners():
    @dg.schedule(
        cron_schedule="@daily", job_name="test_job", owners=["user@example.com", "team:data"]
    )
    def schedule_with_owners(): ...

    assert schedule_with_owners.owners == ["user@example.com", "team:data"]


def test_owners_validation():
    # Test invalid team name with special characters
    with pytest.raises(dg.DagsterInvalidDefinitionError, match="contains invalid characters"):

        @dg.schedule(cron_schedule="@daily", job_name="test_job", owners=["team:bad-name"])
        def schedule_with_bad_team(): ...

    # Test empty team name
    with pytest.raises(dg.DagsterInvalidDefinitionError, match="Team name cannot be empty"):

        @dg.schedule(cron_schedule="@daily", job_name="test_job", owners=["team:"])
        def schedule_with_empty_team(): ...
