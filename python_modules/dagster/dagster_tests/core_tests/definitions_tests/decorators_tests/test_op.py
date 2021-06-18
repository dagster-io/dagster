from dagster import execute_pipeline, graph, op


def test_op():
    @op
    def my_op():
        pass

    @graph
    def my_graph():
        my_op()

    result = execute_pipeline(my_graph.to_job())
    assert result.success
