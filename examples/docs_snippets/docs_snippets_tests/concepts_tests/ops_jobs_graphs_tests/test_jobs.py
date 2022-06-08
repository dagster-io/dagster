from docs_snippets.concepts.ops_jobs_graphs.branching_job import branching
from docs_snippets.concepts.ops_jobs_graphs.dep_dsl import define_dep_dsl_graph
from docs_snippets.concepts.ops_jobs_graphs.dynamic import (
    chained,
    dynamic_graph,
    multiple,
    naive,
    other_arg,
    return_dynamic,
)
from docs_snippets.concepts.ops_jobs_graphs.fan_in_job import fan_in
from docs_snippets.concepts.ops_jobs_graphs.jobs import (
    alias,
    one_plus_one,
    one_plus_one_from_constructor,
    tagged_add_one,
)
from docs_snippets.concepts.ops_jobs_graphs.jobs_from_graphs import local_job, prod_job
from docs_snippets.concepts.ops_jobs_graphs.linear_job import linear
from docs_snippets.concepts.ops_jobs_graphs.multiple_io_job import inputs_and_outputs
from docs_snippets.concepts.ops_jobs_graphs.order_based_dependency_job import (
    nothing_dependency,
)
from docs_snippets.concepts.ops_jobs_graphs.retries import (
    default_and_override_job,
    retry_job,
)


def test_one_plus_one():
    result = one_plus_one.execute_in_process()
    assert result.output_for_node("add_one") == 2


def test_one_plus_one_graph_def():
    result = one_plus_one_from_constructor.execute_in_process()
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


def test_dep_dsl():
    result = define_dep_dsl_graph().execute_in_process(
        run_config={"ops": {"A": {"inputs": {"num": 0}}}}
    )
    assert result.success


def test_dynamic_examples():

    assert naive.execute_in_process().success
    assert dynamic_graph.execute_in_process().success
    assert chained.execute_in_process().success
    assert other_arg.execute_in_process().success
    assert multiple.execute_in_process().success
    assert return_dynamic()


def test_retry_examples():
    # just that they run
    assert retry_job.execute_in_process(raise_on_error=False)
    assert default_and_override_job.execute_in_process(raise_on_error=False)


def test_jobs_from_graphs():
    assert local_job.execute_in_process()
    assert prod_job.execute_in_process()
