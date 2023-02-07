from project_fully_featured import defs


def test_defs_can_load():
    assert defs.get_job_def("activity_analytics_job")
    assert defs.get_job_def("core_job")
    assert defs.get_job_def("story_recommender_job")
