import dagster.check as check
from dagster import (
    DependencyDefinition,
    InputDefinition,
    Int,
    List,
    ModeDefinition,
    MultiDependencyDefinition,
    Nothing,
    Optional,
    Output,
    OutputDefinition,
    PipelineDefinition,
    ResourceDefinition,
    RunConfig,
    String,
    execute_pipeline,
    execute_pipeline_iterator,
    lambda_solid,
    pipeline,
    solid,
)
from dagster.core.definitions import Solid, solids_in_topological_order
from dagster.core.definitions.container import _create_adjacency_lists
from dagster.core.definitions.dependency import DependencyStructure
from dagster.core.execution.api import step_output_event_filter
from dagster.core.execution.results import SolidExecutionResult
from dagster.core.instance import DagsterInstance
from dagster.core.utility_solids import (
    create_root_solid,
    create_solid_with_deps,
    define_stub_solid,
    input_set,
)
from dagster.utils.test import execute_solid_within_pipeline

# protected members
# pylint: disable=W0212


def _default_passthrough_compute_fn(*args, **kwargs):
    check.invariant(not args, 'There should be no positional args')
    return list(kwargs.values())[0]


def create_dep_input_fn(name):
    return lambda context, arg_dict: {name: 'input_set'}


def make_compute_fn():
    def compute(context, inputs):
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
        result.append({context.solid.name: 'compute_called'})
        return result

    return compute


def _do_construct(solids, dependencies):
    solids = {s.name: Solid(name=s.name, definition=s) for s in solids}
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
        name='diamond_pipeline', solid_defs=create_diamond_solids(), dependencies=diamond_deps()
    )


def test_diamond_toposort():
    assert [s.name for s in solids_in_topological_order(create_diamond_pipeline())] == [
        'A_source',
        'A',
        'B',
        'C',
        'D',
    ]


def compute_called(name):
    return {name: 'compute_called'}


def assert_equivalent_results(left, right):
    check.inst_param(left, 'left', SolidExecutionResult)
    check.inst_param(right, 'right', SolidExecutionResult)

    assert left.success == right.success
    assert left.name == right.name
    assert left.solid.name == right.solid.name
    assert left.output_value() == right.output_value()


def assert_all_results_equivalent(expected_results, result_results):
    check.list_param(expected_results, 'expected_results', of_type=SolidExecutionResult)
    check.list_param(result_results, 'result_results', of_type=SolidExecutionResult)
    assert len(expected_results) == len(result_results)
    for expected, result in zip(expected_results, result_results):
        assert_equivalent_results(expected, result)


def test_pipeline_execution_graph_diamond():
    pipe = PipelineDefinition(solid_defs=create_diamond_solids(), dependencies=diamond_deps())
    return _do_test(pipe)


def test_execute_solid_in_diamond():
    solid_result = execute_solid_within_pipeline(
        create_diamond_pipeline(), 'A', inputs={'A_input': [{'a key': 'a value'}]}
    )

    assert solid_result.success
    assert solid_result.output_value() == [{'a key': 'a value'}, {'A': 'compute_called'}]


def test_execute_aliased_solid_in_diamond():
    a_source = define_stub_solid('A_source', [input_set('A_input')])

    @pipeline
    def aliased_pipeline():
        create_root_solid('A').alias('aliased')(a_source())

    solid_result = execute_solid_within_pipeline(
        aliased_pipeline, 'aliased', inputs={'A_input': [{'a key': 'a value'}]}
    )

    assert solid_result.success
    assert solid_result.output_value() == [{'a key': 'a value'}, {'aliased': 'compute_called'}]


def test_create_pipeline_with_empty_solids_list():
    @pipeline
    def empty_pipe():
        pass

    assert execute_pipeline(empty_pipe).success


def test_singleton_pipeline():
    stub_solid = define_stub_solid('stub', [{'a key': 'a value'}])

    @pipeline
    def single_solid_pipeline():
        stub_solid()

    assert execute_pipeline(single_solid_pipeline).success


def test_two_root_solid_pipeline_with_empty_dependency_definition():
    stub_solid_a = define_stub_solid('stub_a', [{'a key': 'a value'}])
    stub_solid_b = define_stub_solid('stub_b', [{'a key': 'a value'}])

    @pipeline
    def pipe():
        stub_solid_a()
        stub_solid_b()

    assert execute_pipeline(pipe).success


def test_two_root_solid_pipeline_with_partial_dependency_definition():
    stub_solid_a = define_stub_solid('stub_a', [{'a key': 'a value'}])
    stub_solid_b = define_stub_solid('stub_b', [{'a key': 'a value'}])

    single_dep_pipe = PipelineDefinition(
        solid_defs=[stub_solid_a, stub_solid_b], dependencies={'stub_a': {}}
    )

    assert execute_pipeline(single_dep_pipe).success


def _do_test(pipe):
    result = execute_pipeline(pipe)

    assert result.result_for_solid('A').output_value() == [
        input_set('A_input'),
        compute_called('A'),
    ]

    assert result.result_for_solid('B').output_value() == [
        input_set('A_input'),
        compute_called('A'),
        compute_called('B'),
    ]

    assert result.result_for_solid('C').output_value() == [
        input_set('A_input'),
        compute_called('A'),
        compute_called('C'),
    ]

    assert result.result_for_solid('D').output_value() == [
        input_set('A_input'),
        compute_called('A'),
        compute_called('C'),
        compute_called('B'),
        compute_called('D'),
    ] or result.result_for_solid('D').output_value() == [
        input_set('A_input'),
        compute_called('A'),
        compute_called('B'),
        compute_called('C'),
        compute_called('D'),
    ]


def test_empty_pipeline_execution():
    result = execute_pipeline(PipelineDefinition(solid_defs=[]))

    assert result.success


def test_pipeline_name_threaded_through_context():
    name = 'foobar'

    @solid()
    def assert_name_solid(context):
        assert context.pipeline_def.name == name

    result = execute_pipeline(PipelineDefinition(name="foobar", solid_defs=[assert_name_solid]))

    assert result.success


def test_pipeline_subset():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid
    def add_one(num):
        return num + 1

    pipeline_def = PipelineDefinition(
        solid_defs=[return_one, add_one],
        dependencies={'add_one': {'num': DependencyDefinition('return_one')}},
    )

    pipeline_result = execute_pipeline(pipeline_def)
    assert pipeline_result.success
    assert pipeline_result.result_for_solid('add_one').output_value() == 2

    env_config = {'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}}

    subset_result = execute_pipeline(
        pipeline_def.build_sub_pipeline(['add_one']), environment_dict=env_config
    )

    assert subset_result.success
    assert len(subset_result.solid_result_list) == 1
    assert subset_result.result_for_solid('add_one').output_value() == 4


def test_pipeline_subset_with_multi_dependency():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid
    def return_two():
        return 2

    @lambda_solid(input_defs=[InputDefinition('dep', Nothing)])
    def noop():
        return 3

    pipeline_def = PipelineDefinition(
        solid_defs=[return_one, return_two, noop],
        dependencies={
            'noop': {
                'dep': MultiDependencyDefinition(
                    [DependencyDefinition('return_one'), DependencyDefinition('return_two')]
                )
            }
        },
    )

    pipeline_result = execute_pipeline(pipeline_def)
    assert pipeline_result.success
    assert pipeline_result.result_for_solid('noop').output_value() == 3

    subset_result = execute_pipeline(pipeline_def.build_sub_pipeline(['noop']))

    assert subset_result.success
    assert len(subset_result.solid_result_list) == 1
    assert pipeline_result.result_for_solid('noop').output_value() == 3

    subset_result = execute_pipeline(
        pipeline_def.build_sub_pipeline(['return_one', 'return_two', 'noop'])
    )

    assert subset_result.success
    assert len(subset_result.solid_result_list) == 3
    assert pipeline_result.result_for_solid('noop').output_value() == 3


def define_three_part_pipeline():
    @lambda_solid(input_defs=[InputDefinition('num', Int)], output_def=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    @lambda_solid(input_defs=[InputDefinition('num', Int)], output_def=OutputDefinition(Int))
    def add_two(num):
        return num + 2

    @lambda_solid(input_defs=[InputDefinition('num', Int)], output_def=OutputDefinition(Int))
    def add_three(num):
        return num + 3

    return PipelineDefinition(name='three_part_pipeline', solid_defs=[add_one, add_two, add_three])


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
        'loggers': {'console': {'config': {'log_level': 'ERROR'}}},
    }

    pipeline_def = define_created_disjoint_three_part_pipeline()

    result = execute_pipeline(
        pipeline_def.build_sub_pipeline(['add_one', 'add_three']), environment_dict=env_config
    )

    assert result.success
    assert len(result.solid_result_list) == 2
    assert result.result_for_solid('add_one').output_value() == 3
    assert result.result_for_solid('add_three').output_value() == 8


def test_pipeline_wrapping_types():
    @lambda_solid(
        input_defs=[InputDefinition('value', Optional[List[Optional[String]]])],
        output_def=OutputDefinition(Optional[List[Optional[String]]]),
    )
    def double_string_for_all(value):
        if not value:
            return value

        output = []
        for item in value:
            output.append(None if item is None else item + item)
        return output

    @pipeline
    def wrapping_test():
        double_string_for_all()

    assert execute_pipeline(
        wrapping_test,
        environment_dict={'solids': {'double_string_for_all': {'inputs': {'value': None}}}},
    ).success

    assert execute_pipeline(
        wrapping_test,
        environment_dict={'solids': {'double_string_for_all': {'inputs': {'value': []}}}},
    ).success

    assert execute_pipeline(
        wrapping_test,
        environment_dict={
            'solids': {'double_string_for_all': {'inputs': {'value': [{'value': 'foo'}]}}}
        },
    ).success

    assert execute_pipeline(
        wrapping_test,
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

    @lambda_solid
    def add_one(num):
        events.append(num + 1)
        return num + 1

    @pipeline
    def test_streaming_iterator():
        add_one(push_one())

    step_event_iterator = step_output_event_filter(
        execute_pipeline_iterator(test_streaming_iterator)
    )

    push_one_step_event = next(step_event_iterator)
    assert push_one_step_event.is_successful_output
    assert events == [1]

    add_one_step_event = next(step_event_iterator)
    assert add_one_step_event.is_successful_output
    assert events == [1, 2]


def test_pipeline_streaming_multiple_outputs():
    events = []

    @solid(output_defs=[OutputDefinition(Int, 'one'), OutputDefinition(Int, 'two')])
    def push_one_two(_context):
        events.append(1)
        yield Output(1, 'one')
        events.append(2)
        yield Output(2, 'two')

    @pipeline
    def test_streaming_iterator_multiple_outputs():
        push_one_two()

    step_event_iterator = step_output_event_filter(
        execute_pipeline_iterator(test_streaming_iterator_multiple_outputs)
    )

    one_output_step_event = next(step_event_iterator)
    assert one_output_step_event.is_successful_output
    assert one_output_step_event.step_output_data.output_name == 'one'
    assert events == [1]

    two_output_step_event = next(step_event_iterator)
    assert two_output_step_event.is_successful_output
    assert two_output_step_event.step_output_data.output_name == 'two'
    assert events == [1, 2]


def test_pipeline_init_failure():
    @solid(required_resource_keys={'failing'})
    def stub_solid(_):
        return None

    env_config = {}

    def failing_resource_fn(*args, **kwargs):
        raise Exception()

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={'failing': ResourceDefinition(resource_fn=failing_resource_fn)}
            )
        ]
    )
    def failing_init_pipeline():
        stub_solid()

    result = execute_pipeline(
        failing_init_pipeline, environment_dict=dict(env_config), raise_on_error=False
    )

    assert result.success is False
    assert len(result.event_list) == 1
    event = result.event_list[0]
    assert event.event_type_value == 'PIPELINE_INIT_FAILURE'
    assert event.pipeline_init_failure_data


def test_reexecution():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid
    def add_one(num):
        return num + 1

    pipeline_def = PipelineDefinition(
        solid_defs=[return_one, add_one],
        dependencies={'add_one': {'num': DependencyDefinition('return_one')}},
    )
    instance = DagsterInstance.ephemeral()
    pipeline_result = execute_pipeline(
        pipeline_def, environment_dict={'storage': {'filesystem': {}}}, instance=instance
    )
    assert pipeline_result.success
    assert pipeline_result.result_for_solid('add_one').output_value() == 2

    reexecution_run_config = RunConfig(previous_run_id=pipeline_result.run_id)
    reexecution_result = execute_pipeline(
        pipeline_def,
        environment_dict={'storage': {'filesystem': {}}},
        run_config=reexecution_run_config,
        instance=instance,
    )

    assert reexecution_result.success
    assert len(reexecution_result.solid_result_list) == 2
    assert reexecution_result.result_for_solid('return_one').output_value() == 1
    assert reexecution_result.result_for_solid('add_one').output_value() == 2


def test_single_step_reexecution():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid
    def add_one(num):
        return num + 1

    pipeline_def = PipelineDefinition(
        solid_defs=[return_one, add_one],
        dependencies={'add_one': {'num': DependencyDefinition('return_one')}},
    )
    instance = DagsterInstance.ephemeral()
    pipeline_result = execute_pipeline(
        pipeline_def, environment_dict={'storage': {'filesystem': {}}}, instance=instance
    )
    assert pipeline_result.success
    assert pipeline_result.result_for_solid('add_one').output_value() == 2

    reexecution_result = execute_pipeline(
        pipeline_def,
        environment_dict={'storage': {'filesystem': {}}},
        run_config=RunConfig(
            previous_run_id=pipeline_result.run_id, step_keys_to_execute=['add_one.compute']
        ),
        instance=instance,
    )

    assert reexecution_result.success
    assert reexecution_result.result_for_solid('return_one').output_value() == None
    assert reexecution_result.result_for_solid('add_one').output_value() == 2


def test_two_step_reexecution():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid
    def add_one(num):
        return num + 1

    @pipeline
    def two_step_reexec():
        add_one(add_one(return_one()))

    instance = DagsterInstance.ephemeral()
    pipeline_result = execute_pipeline(
        two_step_reexec, environment_dict={'storage': {'filesystem': {}}}, instance=instance
    )
    assert pipeline_result.success
    assert pipeline_result.result_for_solid('add_one_2').output_value() == 3

    reexecution_result = execute_pipeline(
        two_step_reexec,
        environment_dict={'storage': {'filesystem': {}}},
        run_config=RunConfig(
            previous_run_id=pipeline_result.run_id,
            step_keys_to_execute=['add_one.compute', 'add_one_2.compute'],
        ),
        instance=instance,
    )

    assert reexecution_result.success
    assert reexecution_result.result_for_solid('return_one').output_value() == None
    assert reexecution_result.result_for_solid('add_one_2').output_value() == 3


def test_optional():
    @solid(output_defs=[OutputDefinition(Int, 'x'), OutputDefinition(Int, 'y', is_optional=True)])
    def return_optional(_context):
        yield Output(1, 'x')

    @lambda_solid
    def echo(x):
        return x

    @pipeline
    def opt_pipeline():
        x, y = return_optional()
        echo.alias('echo_x')(x)
        echo.alias('echo_y')(y)

    pipeline_result = execute_pipeline(opt_pipeline)
    assert pipeline_result.success

    result_required = pipeline_result.result_for_solid('echo_x')
    assert result_required.success

    result_optional = pipeline_result.result_for_solid('echo_y')
    assert not result_optional.success
    assert result_optional.skipped


def test_basic_pipeline_selector():
    @solid
    def def_one(_):
        pass

    # dsl subsets the definitions appropriately
    @pipeline
    def pipe():
        def_one()

    assert pipe.selector.solid_subset == None


def test_selector_with_partial_dependency_dict():
    executed = {}

    @solid
    def def_one(_):
        executed['one'] = True

    @solid
    def def_two(_):
        executed['two'] = True

    pipe_two = PipelineDefinition(
        name='pipe_two', solid_defs=[def_one, def_two], dependencies={'def_one': {}}
    )

    execute_pipeline(pipe_two)

    # if it is in solid defs it will execute even if it is not in dependencies dictionary
    assert set(executed.keys()) == {'one', 'two'}


def test_selector_with_build_sub_pipeline():
    @solid
    def def_one(_):
        pass

    @solid
    def def_two(_):
        pass

    # dsl subsets the definitions appropriately
    @pipeline
    def pipe():
        def_one()
        def_two()

    assert set(pipe.build_sub_pipeline(['def_two']).selector.solid_subset) == {'def_two'}
