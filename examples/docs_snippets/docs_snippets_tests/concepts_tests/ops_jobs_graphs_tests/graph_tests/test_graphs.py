from docs_snippets.concepts.ops_jobs_graphs.graphs.branching_graph import branching
from docs_snippets.concepts.ops_jobs_graphs.graphs.fan_in_graph import fan_in
from docs_snippets.concepts.ops_jobs_graphs.graphs.linear_graph import linear
from docs_snippets.concepts.ops_jobs_graphs.graphs.graphs import (
    alias,
    one_plus_one,
)
from docs_snippets.concepts.ops_jobs_graphs.graphs.multiple_io_graph import (
    inputs_and_outputs,
)
from docs_snippets.concepts.ops_jobs_graphs.graphs.order_based_dependency import (
    nothing_dependency,
)


def test_one_plus_one():
    result = one_plus_one.execute_in_process()
    assert result.output_for_node("add_one") == 2


def test_other_graphs():
    other_graphs = [
        branching,
        inputs_and_outputs,
        nothing_dependency,
        alias,
        linear,
    ]
    for graph in other_graphs:
        result = graph.execute_in_process()
        assert result.success


def test_fan_in():
    result = fan_in.execute_in_process()
    assert result.success
    assert result.output_for_node("sum_fan_in") == 10
