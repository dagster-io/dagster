from dagster import op
from dagster._legacy import pipeline


def test_solid_tags():
    @op(tags={"foo": "bar"})
    def tags_op(_):
        pass

    assert tags_op.tags == {"foo": "bar"}

    @op()
    def no_tags_op(_):
        pass

    assert no_tags_op.tags == {}


def test_pipeline_tags():
    @pipeline(tags={"foo": "bar"})
    def tags_pipeline():
        pass

    assert tags_pipeline.tags == {"foo": "bar"}

    @pipeline()
    def no_tags_pipeline():
        pass

    assert no_tags_pipeline.tags == {}


def test_solid_subset_tags():
    @op
    def noop_op(_):
        pass

    @pipeline(tags={"foo": "bar"})
    def tags_pipeline():
        noop_op()

    assert tags_pipeline.get_pipeline_subset_def({"noop_op"}).tags == {"foo": "bar"}

    @pipeline()
    def no_tags_pipeline():
        noop_op()

    assert no_tags_pipeline.get_pipeline_subset_def({"noop_op"}).tags == {}
