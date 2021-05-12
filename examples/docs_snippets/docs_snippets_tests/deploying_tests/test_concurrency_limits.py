from docs_snippets.deploying.concurrency_limits import (  # pylint: disable=import-error
    important_pipeline,
    less_important_schedule,
)


def test_inclusion():
    assert important_pipeline
    assert less_important_schedule
