from docs_snippets.guides.dagster.reexecution.reexecution_api import (
    result,
    initial_result,
    from_failure_result,
)


def test_reexecution_results():
    assert not initial_result.success
    assert from_failure_result.success
    assert result.success
