import warnings
from datetime import datetime

import pytest
from dagster import (
    DagsterInvalidDefinitionError,
    DailyPartitionsDefinition,
    Definitions,
    ScheduleDefinition,
    asset,
    build_schedule_context,
    build_schedule_from_partitioned_job,
    define_asset_job,
    graph,
    job,
    op,
)
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.metadata.metadata_value import (
    IntMetadataValue,
    MetadataValue,
    TextMetadataValue,
)
from dagster._core.definitions.partitioned_schedule import (
    UnresolvedPartitionedAssetScheduleDefinition,
)
from dagster._core.definitions.run_config import RunConfig
from dagster._core.definitions.run_request import RunRequest


def test_default_name():
    schedule = ScheduleDefinition(job_name="my_pipeline", cron_schedule="0 0 * * *")
    assert schedule.name == "my_pipeline_schedule"


def test_default_name_graph():
    @graph
    def my_graph():
        pass

    schedule = ScheduleDefinition(job=my_graph, cron_schedule="0 0 * * *")
    assert schedule.name == "my_graph_schedule"


def test_default_name_job():
    @graph
    def my_graph():
        pass

    schedule = ScheduleDefinition(job=my_graph.to_job(name="my_job"), cron_schedule="0 0 * * *")
    assert schedule.name == "my_job_schedule"


def test_jobs_attr():
    @graph
    def my_graph():
        pass

    schedule = ScheduleDefinition(job=my_graph, cron_schedule="0 0 * * *")
    assert schedule.job.name == my_graph.name

    schedule = ScheduleDefinition(job_name="my_pipeline", cron_schedule="0 0 * * *")
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="No job was provided to ScheduleDefinition.",
    ):
        schedule.job  # noqa: B018


def test_invalid_cron_schedule():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="invalid cron schedule",
    ):
        schedule = ScheduleDefinition(job_name="my_pipeline", cron_schedule="oopsies * * * *")
        assert schedule.name == "my_pipeline_schedule"


def test_weird_cron_inteval():
    with pytest.warns(
        UserWarning,
        match="cron schedule with an interval greater than the expected range",
    ):
        schedule = ScheduleDefinition(job_name="my_pipeline", cron_schedule="*/90 * * * *")
        assert schedule.name == "my_pipeline_schedule"


def test_invalid_tag_keys():
    # turn off any outer warnings filters, e.g. ignores that are set in pyproject.toml
    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as caught_warnings:
        ScheduleDefinition(
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
    my_schedule = ScheduleDefinition(
        name="my_schedule",
        cron_schedule="* * * * *",
        job_name="test_job",
        run_config=RunConfig(ops={"foo": "bar"}),
    )

    execution_time = datetime(year=2019, month=2, day=27)
    context_with_time = build_schedule_context(scheduled_execution_time=execution_time)

    execution_data = my_schedule.evaluate_tick(context_with_time)
    assert execution_data.run_requests
    assert len(execution_data.run_requests) == 1
    assert execution_data.run_requests[0].run_config["ops"] == {"foo": "bar"}


def test_schedule_run_config_obj_fn() -> None:
    my_schedule = ScheduleDefinition(
        name="my_schedule",
        cron_schedule="* * * * *",
        job_name="test_job",
        run_config_fn=lambda ctx: RunConfig(
            ops={"baz": "qux", "time": ctx.scheduled_execution_time}
        ),
    )

    execution_time = datetime(year=2019, month=2, day=27)
    context_with_time = build_schedule_context(scheduled_execution_time=execution_time)

    execution_data = my_schedule.evaluate_tick(context_with_time)
    assert execution_data.run_requests
    assert len(execution_data.run_requests) == 1
    assert execution_data.run_requests[0].run_config["ops"] == {
        "baz": "qux",
        "time": execution_time,
    }


def test_coerce_graph_def_to_job():
    @op
    def foo(): ...

    @graph
    def bar():
        foo()

    with pytest.warns(DeprecationWarning, match="Passing GraphDefinition"):
        my_schedule = ScheduleDefinition(cron_schedule="* * * * *", job=bar)

    assert isinstance(my_schedule.job, JobDefinition)
    assert my_schedule.job.name == "bar"


def test_tag_transfer_to_run_request():
    tags_and_exec_fn_schedule = ScheduleDefinition(
        cron_schedule="@daily",
        job_name="the_job",
        tags={"foo": "bar"},
        execution_fn=lambda _: RunRequest(),
    )

    tags_and_no_exec_fn_schedule = ScheduleDefinition(
        cron_schedule="@daily",
        job_name="the_job",
        tags={"foo": "bar"},
    )

    execution_time = datetime(year=2019, month=2, day=27)
    context_with_time = build_schedule_context(scheduled_execution_time=execution_time)

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
    @op
    def my_op():
        pass

    @job
    def my_job_1():
        my_op()

    @job
    def my_job_2():
        my_op()

    my_schedule_1 = ScheduleDefinition(
        job=my_job_1, cron_schedule="@daily", tags={"foo": "bar"}, metadata={"baz": "qux"}
    )

    my_schedule_2 = my_schedule_1.with_updated_job(my_job_2)

    assert my_schedule_2.job.name == "my_job_2"
    assert my_schedule_2.cron_schedule == "@daily"
    assert my_schedule_2.tags == {"foo": "bar"}
    assert my_schedule_2.metadata == {"baz": MetadataValue.text("qux")}


def test_with_updated_metadata():
    schedule = ScheduleDefinition(job_name="job", cron_schedule="@daily", metadata={"baz": "qux"})
    assert schedule.metadata == {"baz": MetadataValue.text("qux")}

    blanked = schedule.with_attributes(metadata={})
    assert blanked.metadata == {}

    @job
    def my_job(): ...

    schedule = ScheduleDefinition(job=my_job, cron_schedule="@daily", metadata={"foo": "bar"})
    updated = schedule.with_attributes(metadata={**schedule.metadata, "foo": "baz"})
    assert updated.metadata["foo"] == TextMetadataValue("baz")


def test_unresolved_metadata():
    @asset(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"))
    def asset1(): ...

    asset1_job = define_asset_job("asset1_job", selection=[asset1])
    unresolved_schedule = build_schedule_from_partitioned_job(
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

    defs = Definitions(
        schedules=[updated],
        jobs=[asset1_job],
        assets=[asset1],
    )

    schedule = defs.resolve_schedule_def("my_schedule")
    assert schedule.metadata["foo"] == TextMetadataValue("baz")
    assert schedule.metadata["four"] == IntMetadataValue(4)
