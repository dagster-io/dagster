from dagster import pipeline, solid


def test_solid_tags():
    @solid(tags={"foo": "bar"})
    def tags_solid(_):
        pass

    assert tags_solid.tags == {"foo": "bar"}

    @solid()
    def no_tags_solid(_):
        pass

    assert no_tags_solid.tags == {}


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
    @solid
    def noop_solid(_):
        pass

    @pipeline(tags={"foo": "bar"})
    def tags_pipeline():
        noop_solid()

    assert tags_pipeline.get_pipeline_subset_def({"noop_solid"}).tags == {"foo": "bar"}

    @pipeline()
    def no_tags_pipeline():
        noop_solid()

    assert no_tags_pipeline.get_pipeline_subset_def({"noop_solid"}).tags == {}
