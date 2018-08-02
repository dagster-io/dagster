import pytest

from dagster import (check, config)

from dagster.core.definitions import (SolidDefinition, OutputDefinition, PipelineDefinition)
from dagster.core.graph import (create_adjacency_lists, SolidGraph)
from dagster.core.execution import (
    execute_pipeline_iterator,
    execute_pipeline_iterator_in_memory,
    ExecutionContext,
    SolidExecutionResult,
)

from dagster.utils.compatability import create_custom_source_input

# protected members
# pylint: disable=W0212


def create_test_context():
    return ExecutionContext()


def _default_passthrough_transform(*args, **kwargs):
    check.invariant(not args, 'There should be no positional args')
    return list(kwargs.values())[0]


def create_dep_input_fn(name):
    return lambda context, arg_dict: {name: 'input_set'}


def create_solid_with_deps(name, *solid_deps):
    # def throw_input_fn(arg_dict):
    #     return [{name: 'input_set'}]

    inputs = [
        create_custom_source_input(
            solid_dep.name,
            source_fn=create_dep_input_fn(solid_dep.name),
            argument_def_dict={},
            depends_on=solid_dep,
        ) for solid_dep in solid_deps
    ]

    def dep_transform(_context, args):
        passed_rows = list(args.values())[0]
        passed_rows.append({name: 'transform_called'})
        #return copy.deepcopy(passed_rows)
        return passed_rows

    return SolidDefinition(
        name=name,
        inputs=inputs,
        transform_fn=dep_transform,
        output=OutputDefinition(),
    )


def create_root_solid(name):
    input_name = name + '_input'
    inp = create_custom_source_input(
        input_name,
        source_fn=lambda context, arg_dict: [{input_name: 'input_set'}],
        argument_def_dict={},
    )

    def root_transform(_context, args):
        passed_rows = list(args.values())[0]
        passed_rows.append({name: 'transform_called'})
        #return copy.deepcopy(passed_rows)
        return passed_rows

    return SolidDefinition(
        name=name,
        inputs=[inp],
        transform_fn=root_transform,
        output=OutputDefinition(),
    )


def test_empty_adjaceny_lists():
    forward_edges, backwards_edges = create_adjacency_lists([create_root_solid('a_node')])
    assert forward_edges == {'a_node': set()}
    assert backwards_edges == {'a_node': set()}


def test_single_dep_adjacency_lists():
    # A <-- B
    node_a = create_root_solid('A')
    node_b = create_solid_with_deps('B', node_a)

    forward_edges, backwards_edges = create_adjacency_lists([node_a, node_b])

    assert forward_edges == {'A': {'B'}, 'B': set()}
    assert backwards_edges == {'B': {'A'}, 'A': set()}


def test_diamond_deps_adjaceny_lists():
    # A <-- (B, C) <-- D

    node_a = create_root_solid('A')
    node_b = create_solid_with_deps('B', node_a)
    node_c = create_solid_with_deps('C', node_a)
    node_d = create_solid_with_deps('D', node_b, node_c)

    forward_edges, backwards_edges = create_adjacency_lists([node_a, node_b, node_c, node_d])
    assert forward_edges == {'A': {'B', 'C'}, 'B': {'D'}, 'C': {'D'}, 'D': set()}
    assert backwards_edges == {'D': {'B', 'C'}, 'B': {'A'}, 'C': {'A'}, 'A': set()}


def test_disconnected_graphs_adjaceny_lists():
    # A <-- B
    # C <-- D
    node_a = create_root_solid('A')
    node_b = create_solid_with_deps('B', node_a)

    node_c = create_root_solid('C')
    node_d = create_solid_with_deps('D', node_c)

    forward_edges, backwards_edges = create_adjacency_lists([node_a, node_b, node_c, node_d])
    assert forward_edges == {'A': {'B'}, 'B': set(), 'C': {'D'}, 'D': set()}
    assert backwards_edges == {'B': {'A'}, 'A': set(), 'D': {'C'}, 'C': set()}


def create_diamond_graph():
    node_a = create_root_solid('A')
    node_b = create_solid_with_deps('B', node_a)
    node_c = create_solid_with_deps('C', node_a)
    node_d = create_solid_with_deps('D', node_b, node_c)

    return SolidGraph([node_d, node_c, node_b, node_a])


def test_diamond_toposort():
    graph = create_diamond_graph()
    assert graph.topological_order == ['A', 'B', 'C', 'D']


def test_single_node_unprovided_inputs():
    node_a = create_root_solid('A')
    solid_graph = SolidGraph(solids=[node_a])
    assert solid_graph.compute_unprovided_inputs('A', ['A_input']) == set()
    assert solid_graph.compute_unprovided_inputs('A', []) == set(['A_input'])


def test_diamond_toposort_unprovided_inputs():
    solid_graph = create_diamond_graph()

    # no inputs
    assert solid_graph.compute_unprovided_inputs('A', []) == set(['A_input'])
    assert solid_graph.compute_unprovided_inputs('B', []) == set(['A_input'])
    assert solid_graph.compute_unprovided_inputs('C', []) == set(['A_input'])
    assert solid_graph.compute_unprovided_inputs('D', []) == set(['A_input'])

    # root input
    assert solid_graph.compute_unprovided_inputs('A', ['A_input']) == set()
    assert solid_graph.compute_unprovided_inputs('B', ['A_input']) == set()
    assert solid_graph.compute_unprovided_inputs('C', ['A_input']) == set()
    assert solid_graph.compute_unprovided_inputs('D', ['A_input']) == set()

    # immediate input
    assert solid_graph.compute_unprovided_inputs('A', ['A_input']) == set()
    assert solid_graph.compute_unprovided_inputs('B', ['A']) == set()
    assert solid_graph.compute_unprovided_inputs('C', ['A']) == set()
    assert solid_graph.compute_unprovided_inputs('D', ['B', 'C']) == set()

    # mixed satisified inputs
    assert solid_graph.compute_unprovided_inputs('D', ['A_input', 'C']) == set()
    assert solid_graph.compute_unprovided_inputs('D', ['B', 'A_input']) == set()

    # mixed unsatisifed inputs
    assert solid_graph.compute_unprovided_inputs('D', ['C']) == set(['A_input'])
    assert solid_graph.compute_unprovided_inputs('D', ['B']) == set(['A_input'])


def test_unprovided_input_param_invariants():
    node_a = create_root_solid('A')
    solid_graph = SolidGraph(solids=[node_a])

    with pytest.raises(check.ParameterCheckError):
        solid_graph.compute_unprovided_inputs('B', [])

    with pytest.raises(check.ParameterCheckError):
        solid_graph.compute_unprovided_inputs('A', ['no_input_here'])


def test_execution_subgraph_one_node():
    node_a = create_root_solid('A')
    solid_graph = SolidGraph(solids=[node_a])

    execution_graph = solid_graph.create_execution_subgraph(
        from_solids=['A'],
        to_solids=['A'],
    )
    assert execution_graph


def test_execution_graph_diamond():
    solid_graph = create_diamond_graph()

    full_execution_graph = solid_graph.create_execution_subgraph(
        from_solids=['A'],
        to_solids=['D'],
    )
    assert full_execution_graph.topological_order == ['A', 'B', 'C', 'D']
    assert len(full_execution_graph._solid_dict) == 4

    d_only_graph = solid_graph.create_execution_subgraph(
        from_solids=['D'],
        to_solids=['D'],
    )
    assert len(d_only_graph._solid_dict) == 1
    assert d_only_graph.topological_order == ['D']

    abc_graph = solid_graph.create_execution_subgraph(
        from_solids=['B', 'C'],
        to_solids=['D'],
    )
    assert len(abc_graph._solid_dict) == 3
    assert abc_graph.topological_order == ['B', 'C', 'D']


def input_set(name):
    return {name: 'input_set'}


def transform_called(name):
    return {name: 'transform_called'}


def assert_equivalent_results(left, right):
    check.inst_param(left, 'left', SolidExecutionResult)
    check.inst_param(right, 'right', SolidExecutionResult)

    assert left.success == right.success
    assert left.name == right.name
    assert left.solid.name == right.solid.name
    assert left.transformed_value == right.transformed_value


def assert_all_results_equivalent(expected_results, result_results):
    check.list_param(expected_results, 'expected_results', of_type=SolidExecutionResult)
    check.list_param(result_results, 'result_results', of_type=SolidExecutionResult)
    assert len(expected_results) == len(result_results)
    for expected, result in zip(expected_results, result_results):
        assert_equivalent_results(expected, result)


def test_pipeline_execution_graph_diamond():
    solid_graph = create_diamond_graph()
    pipeline = PipelineDefinition(solids=solid_graph.solids)
    environment = config.Environment(sources={'A': {'A_input': config.Source('CUSTOM', {})}})
    return _do_test(pipeline, lambda: execute_pipeline_iterator(
        pipeline,
        environment=environment,
    ))


def test_pipeline_execution_graph_diamond_in_memory():
    solid_graph = create_diamond_graph()
    pipeline = PipelineDefinition(solids=solid_graph.solids)
    input_values = {'A_input': [{'A_input': 'input_set'}]}
    return _do_test(pipeline, lambda: execute_pipeline_iterator_in_memory(
        ExecutionContext(),
        pipeline,
        input_values=input_values,
    ))


def _do_test(pipeline, do_execute_pipeline_iter):
    solid_graph = create_diamond_graph()

    pipeline = PipelineDefinition(solids=solid_graph.solids)

    results = list()

    for result in do_execute_pipeline_iter():
        results.append(result.copy())

    assert results[0].transformed_value[0] == input_set('A_input')
    assert results[0].transformed_value[1] == transform_called('A')

    assert results[0].transformed_value == [input_set('A_input'), transform_called('A')]

    expected_results = [
        SolidExecutionResult(
            success=True,
            solid=pipeline.solid_named('A'),
            transformed_value=[
                input_set('A_input'),
                transform_called('A'),
            ],
            exception=None,
        ),
        SolidExecutionResult(
            success=True,
            solid=pipeline.solid_named('B'),
            transformed_value=[
                input_set('A_input'),
                transform_called('A'),
                transform_called('B'),
            ],
            exception=None,
        ),
        SolidExecutionResult(
            success=True,
            solid=pipeline.solid_named('C'),
            transformed_value=[
                input_set('A_input'),
                transform_called('A'),
                transform_called('B'),
                transform_called('C'),
            ],
            exception=None,
        ),
        SolidExecutionResult(
            success=True,
            solid=pipeline.solid_named('D'),
            transformed_value=[
                input_set('A_input'),
                transform_called('A'),
                transform_called('B'),
                transform_called('C'),
                transform_called('D'),
            ],
            exception=None,
        ),
    ]

    assert_all_results_equivalent(expected_results, results)
