from docs_snippets_crag.concepts.solids_pipelines.branching_pipeline import branching
from docs_snippets_crag.concepts.solids_pipelines.dep_dsl import define_dep_dsl_graph
from docs_snippets_crag.concepts.solids_pipelines.dynamic_pipeline.dynamic_pipeline import (
    process_directory,
)
from docs_snippets_crag.concepts.solids_pipelines.fan_in_pipeline import fan_in
from docs_snippets_crag.concepts.solids_pipelines.linear_pipeline import linear
from docs_snippets_crag.concepts.solids_pipelines.multiple_io_pipeline import inputs_and_outputs
from docs_snippets_crag.concepts.solids_pipelines.order_based_dependency_pipeline import (
    nothing_dependency,
)
from docs_snippets_crag.concepts.solids_pipelines.pipelines import (
    alias,
    one_plus_one,
    one_plus_one_graph_def,
    tagged_add_one,
)


def test_one_plus_one():
    result = one_plus_one.execute_in_process()
    assert result.output_for_node("add_one") == 2


def test_one_plus_one_graph_def():
    result = one_plus_one_graph_def.execute_in_process()
    assert result.output_for_node("add_one") == 2


def test_linear():
    result = linear.execute_in_process()
    assert result.output_for_node("add_one_3") == 4


def test_other_graphs():
    other_graphs = [
        branching,
        inputs_and_outputs,
        nothing_dependency,
        alias,
        tagged_add_one,
    ]
    for graph in other_graphs:
        result = graph.execute_in_process()
        assert result.success


def test_fan_in():
    result = fan_in.execute_in_process()
    assert result.success
    assert result.output_for_node("sum_fan_in") == 10


def test_dynamic():
    result = process_directory.execute_in_process()
    assert result.success


def test_dep_dsl():
    result = define_dep_dsl_graph().execute_in_process(
        run_config={"ops": {"A": {"inputs": {"num": 0}}}}
    )
    assert result.success
