from docs_snippets.guides.dagster.reexecution.reexecution_api import (
    from_failure_result,
    initial_result,
    result,
)


def test_reexecution_results():
    assert not initial_result.success
    assert from_failure_result.success
    assert result.success
