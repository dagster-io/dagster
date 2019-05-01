import dagster.check as check

from dagster import (
    DependencyDefinition,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    Result,
    SolidDefinition,
    SolidInstance,
    execute_pipeline,
    execute_pipeline_iterator,
    lambda_solid,
    solid,
)

from dagster.core.types import Nullable, List, String

from dagster.core.definitions import Solid, solids_in_topological_order
from dagster.core.definitions.dependency import DependencyStructure
from dagster.core.definitions.pipeline import _create_adjacency_lists

from dagster.core.execution import SolidExecutionResult, step_output_event_filter

from dagster.core.utility_solids import define_stub_solid

from dagster.utils.test import execute_solid

# protected members
# pylint: disable=W0212


def _default_passthrough_transform(*args, **kwargs):
    check.invariant(not args, 'There should be no positional args')
    return list(kwargs.values())[0]


def create_dep_input_fn(name):
    return lambda context, arg_dict: {name: 'input_set'}


def make_transform():
    def transform(context, inputs):
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
        result.append({context.solid.name: 'transform_called'})
        return result

    return transform


def _transform_fn(context, inputs):
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
    result.append({context.solid.name: 'transform_called'})
    yield Result(result)


def create_solid_with_deps(name, *solid_deps):
    inputs = [InputDefinition(solid_dep.name) for solid_dep in solid_deps]

    return SolidDefinition(
        name=name, inputs=inputs, transform_fn=_transform_fn, outputs=[OutputDefinition()]
    )


def create_root_solid(name):
    input_name = name + '_input'
    inp = InputDefinition(input_name)

    return SolidDefinition(
        name=name, inputs=[inp], transform_fn=_transform_fn, outputs=[OutputDefinition()]
    )


def _do_construct(solids, dependencies):
    solids = {
        s.name: Solid(
            name=s.name, definition=s, resource_mapper_fn=SolidInstance.default_resource_mapper_fn
        )
        for s in solids
    }
    dependency_structure = DependencyStructure.from_definitions(solids, dependencies)
    return _create_adjacency_lists(list(solids.values()), dependency_structure)


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
        [node_a, node_b], {'B': {'A': DependencyDefinition('A')}}
    )

    assert forward_edges == {'A': {'B'}, 'B': set()}
    assert backwards_edges == {'B': {'A'}, 'A': set()}


def test_diamond_deps_adjaceny_lists():
    forward_edges, backwards_edges = _do_construct(create_diamond_solids(), diamond_deps())

    assert forward_edges == {'A_source': {'A'}, 'A': {'B', 'C'}, 'B': {'D'}, 'C': {'D'}, 'D': set()}
    assert backwards_edges == {
        'D': {'B', 'C'},
        'B': {'A'},
        'C': {'A'},
        'A': {'A_source'},
        'A_source': set(),
    }


def diamond_deps():
    return {
        'A': {'A_input': DependencyDefinition('A_source')},
        'B': {'A': DependencyDefinition('A')},
        'C': {'A': DependencyDefinition('A')},
        'D': {'B': DependencyDefinition('B'), 'C': DependencyDefinition('C')},
    }


def test_disconnected_graphs_adjaceny_lists():
    # A <-- B
    # C <-- D
    node_a = create_root_solid('A')
    node_b = create_solid_with_deps('B', node_a)

    node_c = create_root_solid('C')
    node_d = create_solid_with_deps('D', node_c)

    forward_edges, backwards_edges = _do_construct(
        [node_a, node_b, node_c, node_d],
        {'B': {'A': DependencyDefinition('A')}, 'D': {'C': DependencyDefinition('C')}},
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


def create_diamond_pipeline():
    return PipelineDefinition(
        name='diamond_pipeline', solids=create_diamond_solids(), dependencies=diamond_deps()
    )


def test_diamond_toposort():
    assert [s.name for s in solids_in_topological_order(create_diamond_pipeline())] == [
        'A_source',
        'A',
        'B',
        'C',
        'D',
    ]


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
    return _do_test(pipeline)


def test_execute_solid_in_diamond():
    solid_result = execute_solid(
        create_diamond_pipeline(), 'A', inputs={'A_input': [{'a key': 'a value'}]}
    )

    assert solid_result.success
    assert solid_result.transformed_value() == [{'a key': 'a value'}, {'A': 'transform_called'}]


def test_execute_aliased_solid_in_diamond():
    a_source = define_stub_solid('A_source', [input_set('A_input')])
    pipeline_def = PipelineDefinition(
        name='aliased_pipeline',
        solids=[a_source, create_root_solid('A')],
        dependencies={
            SolidInstance('A', alias='aliased'): {'A_input': DependencyDefinition(a_source.name)}
        },
    )

    solid_result = execute_solid(
        pipeline_def, 'aliased', inputs={'A_input': [{'a key': 'a value'}]}
    )

    assert solid_result.success
    assert solid_result.transformed_value() == [
        {'a key': 'a value'},
        {'aliased': 'transform_called'},
    ]


def test_create_pipeline_with_empty_solids_list():
    single_solid_pipeline = PipelineDefinition(solids=[], dependencies={})

    result = execute_pipeline(single_solid_pipeline)
    assert result.success


def test_singleton_pipeline():
    stub_solid = define_stub_solid('stub', [{'a key': 'a value'}])
    single_solid_pipeline = PipelineDefinition(solids=[stub_solid], dependencies={})

    result = execute_pipeline(single_solid_pipeline)
    assert result.success


def test_two_root_solid_pipeline_with_empty_dependency_definition():
    stub_solid_a = define_stub_solid('stub_a', [{'a key': 'a value'}])
    stub_solid_b = define_stub_solid('stub_b', [{'a key': 'a value'}])
    single_solid_pipeline = PipelineDefinition(solids=[stub_solid_a, stub_solid_b], dependencies={})

    result = execute_pipeline(single_solid_pipeline)
    assert result.success


def test_two_root_solid_pipeline_with_partial_dependency_definition():
    stub_solid_a = define_stub_solid('stub_a', [{'a key': 'a value'}])
    stub_solid_b = define_stub_solid('stub_b', [{'a key': 'a value'}])
    single_solid_pipeline = PipelineDefinition(
        solids=[stub_solid_a, stub_solid_b], dependencies={'stub_a': {}}
    )

    result = execute_pipeline(single_solid_pipeline)
    assert result.success


def _do_test(pipeline):
    result = execute_pipeline(pipeline)

    assert result.result_for_solid('A').transformed_value() == [
        input_set('A_input'),
        transform_called('A'),
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


def test_pipeline_name_threaded_through_context():
    name = 'foobar'

    @solid()
    def assert_name_transform(context):
        assert context.pipeline_def.name == name

    result = execute_pipeline(PipelineDefinition(name="foobar", solids=[assert_name_transform]))

    assert result.success

    for step_event in step_output_event_filter(
        execute_pipeline_iterator(
            PipelineDefinition(name="foobar", solids=[assert_name_transform]), {}
        )
    ):
        assert step_event.is_step_success


def test_pipeline_subset():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(inputs=[InputDefinition('num')])
    def add_one(num):
        return num + 1

    pipeline_def = PipelineDefinition(
        solids=[return_one, add_one],
        dependencies={'add_one': {'num': DependencyDefinition('return_one')}},
    )

    pipeline_result = execute_pipeline(pipeline_def)
    assert pipeline_result.success
    assert pipeline_result.result_for_solid('add_one').transformed_value() == 2

    env_config = {'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}}

    subset_result = execute_pipeline(
        pipeline_def.build_sub_pipeline(['add_one']), environment_dict=env_config
    )

    assert subset_result.success
    assert len(subset_result.solid_result_list) == 1
    assert subset_result.result_for_solid('add_one').transformed_value() == 4

    events = execute_pipeline_iterator(
        pipeline_def.build_sub_pipeline(['add_one']), environment_dict=env_config
    )

    for step_event in step_output_event_filter(events):
        assert step_event.is_step_success


def define_three_part_pipeline():
    @lambda_solid(inputs=[InputDefinition('num', Int)], output=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    @lambda_solid(inputs=[InputDefinition('num', Int)], output=OutputDefinition(Int))
    def add_two(num):
        return num + 2

    @lambda_solid(inputs=[InputDefinition('num', Int)], output=OutputDefinition(Int))
    def add_three(num):
        return num + 3

    return PipelineDefinition(name='three_part_pipeline', solids=[add_one, add_two, add_three])


def define_created_disjoint_three_part_pipeline():
    return define_three_part_pipeline().build_sub_pipeline(['add_one', 'add_three'])


def test_pipeline_disjoint_subset():
    disjoint_pipeline = define_three_part_pipeline().build_sub_pipeline(['add_one', 'add_three'])
    assert len(disjoint_pipeline.solids) == 2


def test_pipeline_execution_disjoint_subset():
    env_config = {
        'solids': {
            'add_one': {'inputs': {'num': {'value': 2}}},
            'add_three': {'inputs': {'num': {'value': 5}}},
        },
        'context': {'default': {'config': {'log_level': 'ERROR'}}},
    }

    pipeline_def = define_created_disjoint_three_part_pipeline()

    result = execute_pipeline(
        pipeline_def.build_sub_pipeline(['add_one', 'add_three']), environment_dict=env_config
    )

    assert result.success

    assert len(result.solid_result_list) == 2

    assert result.result_for_solid('add_one').transformed_value() == 3
    assert result.result_for_solid('add_three').transformed_value() == 8


def test_pipeline_wrapping_types():
    @lambda_solid(
        inputs=[InputDefinition('value', Nullable(List(Nullable(String))))],
        output=OutputDefinition(Nullable(List(Nullable(String)))),
    )
    def double_string_for_all(value):
        if not value:
            return value

        output = []
        for item in value:
            output.append(None if item is None else item + item)
        return output

    pipeline_def = PipelineDefinition(name='wrapping_test', solids=[double_string_for_all])

    assert execute_pipeline(
        pipeline_def,
        environment_dict={'solids': {'double_string_for_all': {'inputs': {'value': None}}}},
    ).success

    assert execute_pipeline(
        pipeline_def,
        environment_dict={'solids': {'double_string_for_all': {'inputs': {'value': []}}}},
    ).success

    assert execute_pipeline(
        pipeline_def,
        environment_dict={
            'solids': {'double_string_for_all': {'inputs': {'value': [{'value': 'foo'}]}}}
        },
    ).success

    assert execute_pipeline(
        pipeline_def,
        environment_dict={
            'solids': {'double_string_for_all': {'inputs': {'value': [{'value': 'bar'}, None]}}}
        },
    ).success


def test_pipeline_streaming_iterator():
    events = []

    @lambda_solid
    def push_one():
        events.append(1)
        return 1

    @lambda_solid(inputs=[InputDefinition('num')])
    def add_one(num):
        events.append(num + 1)
        return num + 1

    pipeline_def = PipelineDefinition(
        name='test_streaming_iterator',
        solids=[push_one, add_one],
        dependencies={'add_one': {'num': DependencyDefinition('push_one')}},
    )

    step_event_iterator = step_output_event_filter(execute_pipeline_iterator(pipeline_def))

    push_one_step_event = next(step_event_iterator)
    assert push_one_step_event.is_successful_output
    assert push_one_step_event.step_output_data.value_repr == '1'
    assert events == [1]

    add_one_step_event = next(step_event_iterator)
    assert add_one_step_event.is_successful_output
    assert add_one_step_event.step_output_data.value_repr == '2'
    assert events == [1, 2]


def test_pipeline_streaming_multiple_outputs():
    events = []

    @solid(outputs=[OutputDefinition(Int, 'one'), OutputDefinition(Int, 'two')])
    def push_one_two(_context):
        events.append(1)
        yield Result(1, 'one')
        events.append(2)
        yield Result(2, 'two')

    pipeline_def = PipelineDefinition(
        name='test_streaming_iterator_multiple_outputs', solids=[push_one_two]
    )

    step_event_iterator = step_output_event_filter(execute_pipeline_iterator(pipeline_def))

    one_output_step_event = next(step_event_iterator)
    assert one_output_step_event.is_successful_output
    assert one_output_step_event.step_output_data.value_repr == '1'
    assert one_output_step_event.step_output_data.output_name == 'one'
    assert events == [1]

    two_output_step_event = next(step_event_iterator)
    assert two_output_step_event.is_successful_output
    assert two_output_step_event.step_output_data.value_repr == '2'
    assert two_output_step_event.step_output_data.output_name == 'two'
    assert events == [1, 2]
