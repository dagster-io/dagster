from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    check,
    config,
    execute_pipeline,
    SolidInstance,
)

from dagster.core.definitions import (
    DependencyStructure,
    ExecutionGraph,
    _create_adjacency_lists,
    Solid,
)

from dagster.core.execution import (
    execute_pipeline_iterator,
    ExecutionContext,
    SolidExecutionResult,
    PipelineExecutionResult,
)

from dagster.core.test_utils import single_output_transform

from dagster.core.utility_solids import define_stub_solid

# protected members
# pylint: disable=W0212


def _default_passthrough_transform(*args, **kwargs):
    check.invariant(not args, 'There should be no positional args')
    return list(kwargs.values())[0]


def create_dep_input_fn(name):
    return lambda context, arg_dict: {name: 'input_set'}


def make_transform(name):
    def transform(_context, inputs):
        passed_rows = []
        seen = set()
        for row in inputs.values():
            for item in row:
                key = list(item.keys())[0]
                if key not in seen:
                    seen.add(key)
                    passed_rows.append(item)

        result = []
        result.extend(passed_rows)
        result.append({name: 'transform_called'})
        return result

    return transform


def create_solid_with_deps(name, *solid_deps):
    inputs = [InputDefinition(solid_dep.name) for solid_dep in solid_deps]

    return single_output_transform(
        name=name,
        inputs=inputs,
        transform_fn=make_transform(name),
        output=OutputDefinition(),
    )


def create_root_solid(name):
    input_name = name + '_input'
    inp = InputDefinition(input_name)

    return single_output_transform(
        name=name,
        inputs=[inp],
        transform_fn=make_transform(name),
        output=OutputDefinition(),
    )


def _do_construct(solids, dependencies):
    solids = [Solid(name=solid.name, definition=solid) for solid in solids]
    dependency_structure = DependencyStructure.from_definitions(solids, dependencies)
    return _create_adjacency_lists(solids, dependency_structure)


def test_empty_adjaceny_lists():
    solids = [create_root_solid('a_node')]
    forward_edges, backwards_edges = _do_construct(solids, {})
    assert forward_edges == {'a_node': set()}
    assert backwards_edges == {'a_node': set()}


def test_single_dep_adjacency_lists():
    # A <-- B
    node_a = create_root_solid('A')
    node_b = create_solid_with_deps('B', node_a)

    forward_edges, backwards_edges = _do_construct(
        [node_a, node_b],
        {
            'B': {
                'A': DependencyDefinition('A'),
            },
        },
    )

    assert forward_edges == {'A': {'B'}, 'B': set()}
    assert backwards_edges == {'B': {'A'}, 'A': set()}


def graph_from_solids_only(solids, dependencies):
    pipeline = PipelineDefinition(solids=solids, dependencies=dependencies)
    return ExecutionGraph.from_pipeline(pipeline)


def test_diamond_deps_adjaceny_lists():
    forward_edges, backwards_edges = _do_construct(
        create_diamond_solids(),
        diamond_deps(),
    )

    assert forward_edges == {'A_source': {'A'}, 'A': {'B', 'C'}, 'B': {'D'}, 'C': {'D'}, 'D': set()}
    assert backwards_edges == {
        'D': {'B', 'C'},
        'B': {'A'},
        'C': {'A'},
        'A': {'A_source'},
        'A_source': set()
    }


def diamond_deps():
    return {
        'A': {
            'A_input': DependencyDefinition('A_source'),
        },
        'B': {
            'A': DependencyDefinition('A')
        },
        'C': {
            'A': DependencyDefinition('A')
        },
        'D': {
            'B': DependencyDefinition('B'),
            'C': DependencyDefinition('C'),
        }
    }


def test_disconnected_graphs_adjaceny_lists():
    # A <-- B
    # C <-- D
    node_a = create_root_solid('A')
    node_b = create_solid_with_deps('B', node_a)

    node_c = create_root_solid('C')
    node_d = create_solid_with_deps('D', node_c)

    forward_edges, backwards_edges = _do_construct(
        [node_a, node_b, node_c, node_d], {
            'B': {
                'A': DependencyDefinition('A')
            },
            'D': {
                'C': DependencyDefinition('C'),
            }
        }
    )
    assert forward_edges == {'A': {'B'}, 'B': set(), 'C': {'D'}, 'D': set()}
    assert backwards_edges == {'B': {'A'}, 'A': set(), 'D': {'C'}, 'C': set()}


def create_diamond_solids():
    a_source = define_stub_solid('A_source', [input_set('A_input')])
    node_a = create_root_solid('A')
    node_b = create_solid_with_deps('B', node_a)
    node_c = create_solid_with_deps('C', node_a)
    node_d = create_solid_with_deps('D', node_b, node_c)
    return [node_d, node_c, node_b, node_a, a_source]


def create_diamond_graph():
    return graph_from_solids_only(create_diamond_solids(), diamond_deps())


def test_diamond_toposort():
    graph = create_diamond_graph()
    assert graph.topological_order == ['A_source', 'A', 'B', 'C', 'D']


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
    pipeline = PipelineDefinition(solids=create_diamond_solids(), dependencies=diamond_deps())
    environment = config.Environment()
    return _do_test(pipeline, lambda: execute_pipeline_iterator(
        pipeline,
        environment=environment,
    ))


def test_create_single_solid_pipeline():
    stub_solid = define_stub_solid('stub', [{'a key': 'a value'}])
    single_solid_pipeline = PipelineDefinition.create_single_solid_pipeline(
        PipelineDefinition(solids=create_diamond_solids(), dependencies=diamond_deps()),
        'A',
        {
            'A': {
                'A_input': stub_solid,
            },
        },
    )

    result = execute_pipeline(single_solid_pipeline)
    assert result.success


def test_create_single_solid_pipeline_with_alias():
    a_source = define_stub_solid('A_source', [input_set('A_input')])
    stub_solid = define_stub_solid('stub', [{'a_key': 'stubbed_thing'}])
    single_solid_pipeline = PipelineDefinition.create_single_solid_pipeline(
        PipelineDefinition(
            solids=[a_source, create_root_solid('A')],
            dependencies={
                SolidInstance('A', alias='aliased'): {
                    'A_input': DependencyDefinition(a_source.name)
                },
            },
        ),
        'aliased',
        {
            'aliased': {
                'A_input': stub_solid,
            },
        },
    )

    result = execute_pipeline(single_solid_pipeline)
    assert result.success

    expected = [{'a_key': 'stubbed_thing'}, {'A': 'transform_called'}]
    assert result.result_for_solid('aliased').transformed_value() == expected


def _do_test(pipeline, do_execute_pipeline_iter):

    results = list()

    for result in do_execute_pipeline_iter():
        results.append(result)

    result = PipelineExecutionResult(pipeline, ExecutionContext(), results)

    assert result.result_for_solid('A').transformed_value() == [
        input_set('A_input'), transform_called('A')
    ]

    assert result.result_for_solid('B').transformed_value() == [
        input_set('A_input'),
        transform_called('A'),
        transform_called('B'),
    ]

    assert result.result_for_solid('C').transformed_value() == [
        input_set('A_input'),
        transform_called('A'),
        transform_called('C'),
    ]

    assert result.result_for_solid('D').transformed_value() == [
        input_set('A_input'),
        transform_called('A'),
        transform_called('C'),
        transform_called('B'),
        transform_called('D'),
    ] or result.result_for_solid('D').transformed_value() == [
        input_set('A_input'),
        transform_called('A'),
        transform_called('B'),
        transform_called('C'),
        transform_called('D'),
    ]


def test_empty_pipeline_execution():
    result = execute_pipeline(PipelineDefinition(solids=[]))

    assert result.success
