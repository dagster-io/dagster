from project_fully_featured.definitions import defs


def test_defs_can_load() -> None:
    assert defs.resolve_job_def("activity_analytics_job")
    assert defs.resolve_job_def("core_job")
    assert defs.resolve_job_def("story_recommender_job")
