import pytest

from dagster import ScheduleDefinition, graph
from dagster.core.errors import DagsterInvalidDefinitionError


def test_default_name():
    schedule = ScheduleDefinition(pipeline_name="my_pipeline", cron_schedule="0 0 * * *")
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

    schedule = ScheduleDefinition(pipeline_name="my_pipeline", cron_schedule="0 0 * * *")
    with pytest.raises(
        DagsterInvalidDefinitionError, match="No job was provided to ScheduleDefinition."
    ):
        schedule.job  # pylint: disable=pointless-statement
