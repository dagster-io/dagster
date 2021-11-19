from docs_snippets.getting_started.hello_world import hello_dagster


def test_hello_dagster():
    assert hello_dagster.execute_in_process().success
