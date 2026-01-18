import dagster as dg
import pytest
from dagster._core.storage.tags import RESUME_RETRY_TAG, RETRY_STRATEGY_TAG


def test_op_tags():
    @dg.op(tags={"foo": "bar"})
    def tags_op(_):
        pass

    assert tags_op.tags == {"foo": "bar"}

    @dg.op()
    def no_tags_op(_):
        pass

    assert no_tags_op.tags == {}


def test_job_tags():
    @dg.job(tags={"foo": "bar"})
    def tags_job():
        pass

    assert tags_job.tags == {"foo": "bar"}

    @dg.job
    def no_tags_job():
        pass

    assert no_tags_job.tags == {}


def test_op_subset_tags():
    @dg.op
    def noop_op(_):
        pass

    @dg.job(tags={"foo": "bar"})
    def tags_job():
        noop_op()

    assert tags_job.get_subset(op_selection=["noop_op"]).tags == {"foo": "bar"}

    @dg.job
    def no_tags_job():
        noop_op()

    assert no_tags_job.get_subset(op_selection=["noop_op"]).tags == {}


def test_user_editable_system_tags():
    @dg.op
    def noop_op(_):
        pass

    @dg.job
    def noop_job():
        noop_op()

    dg.ScheduleDefinition(
        job=noop_job, cron_schedule="* * * * *", tags={RETRY_STRATEGY_TAG: "ALL_STEPS"}
    )

    with pytest.raises(
        dg.DagsterInvalidDefinitionError, match="Attempted to set tag with reserved system prefix"
    ):
        dg.ScheduleDefinition(
            job=noop_job, cron_schedule="* * * * *", tags={RESUME_RETRY_TAG: "true"}
        )
