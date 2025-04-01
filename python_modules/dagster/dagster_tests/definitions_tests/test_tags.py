import pytest
from dagster import ScheduleDefinition, job, op
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.storage.tags import RESUME_RETRY_TAG, RETRY_STRATEGY_TAG


def test_op_tags():
    @op(tags={"foo": "bar"})
    def tags_op(_):
        pass

    assert tags_op.tags == {"foo": "bar"}

    @op()
    def no_tags_op(_):
        pass

    assert no_tags_op.tags == {}


def test_job_tags():
    @job(tags={"foo": "bar"})
    def tags_job():
        pass

    assert tags_job.tags == {"foo": "bar"}

    @job
    def no_tags_job():
        pass

    assert no_tags_job.tags == {}


def test_op_subset_tags():
    @op
    def noop_op(_):
        pass

    @job(tags={"foo": "bar"})
    def tags_job():
        noop_op()

    assert tags_job.get_subset(op_selection=["noop_op"]).tags == {"foo": "bar"}

    @job
    def no_tags_job():
        noop_op()

    assert no_tags_job.get_subset(op_selection=["noop_op"]).tags == {}


def test_user_editable_system_tags():
    @op
    def noop_op(_):
        pass

    @job
    def noop_job():
        noop_op()

    ScheduleDefinition(
        job=noop_job, cron_schedule="* * * * *", tags={RETRY_STRATEGY_TAG: "ALL_STEPS"}
    )

    with pytest.raises(
        DagsterInvalidDefinitionError, match="Attempted to set tag with reserved system prefix"
    ):
        ScheduleDefinition(job=noop_job, cron_schedule="* * * * *", tags={RESUME_RETRY_TAG: "true"})
