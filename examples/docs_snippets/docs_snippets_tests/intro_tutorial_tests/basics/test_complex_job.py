from docs_snippets.intro_tutorial.basics.connecting_ops.complex_job import diamond


def test_complex_graph():
    result = diamond.execute_in_process()
    assert result.success
