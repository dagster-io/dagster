from docs_snippets.tutorial.scheduling.with_job import with_job
from docs_snippets.tutorial.scheduling.with_schedule import with_schedule


def test_job_defs_can_load():
    assert with_job.defs.get_job_def("hackernews_job")


def test_scheduled_defs_can_load():
    assert with_schedule.defs.get_job_def("hackernews_job")
    assert with_schedule.defs.get_schedule_def("hackernews_job_schedule")
