from docs_snippets.tutorial.scheduling.with_schedule import with_schedule


def test_scheduled_defs_can_load():
    assert with_schedule.defs.get_schedule_def("hackernews_schedule")
