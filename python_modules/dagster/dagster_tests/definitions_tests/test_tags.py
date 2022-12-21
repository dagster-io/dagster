from dagster import job, op


def test_solid_tags():
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


def test_solid_subset_tags():
    @op
    def noop_op(_):
        pass

    @job(tags={"foo": "bar"})
    def tags_job():
        noop_op()

    assert tags_job.get_job_def_for_subset_selection(op_selection=["noop_op"]).tags == {
        "foo": "bar"
    }

    @job
    def no_tags_job():
        noop_op()

    assert no_tags_job.get_pipeline_subset_def({"noop_op"}).tags == {}
