import warnings

import pytest
from dagster import ScheduleDefinition, graph
from dagster._core.errors import DagsterInvalidDefinitionError


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
