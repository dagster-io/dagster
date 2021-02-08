import uuid

import pytest
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
    String,
    check,
    execute_pipeline,
    execute_pipeline_iterator,
    lambda_solid,
    pipeline,
    reexecute_pipeline,
    solid,
)
from dagster.cli.workspace.load import location_origin_from_python_file
from dagster.core.definitions import Solid
from dagster.core.definitions.dependency import DependencyStructure
from dagster.core.definitions.graph import _create_adjacency_lists
from dagster.core.errors import DagsterExecutionStepNotFoundError, DagsterInvariantViolationError
from dagster.core.execution.results import SolidExecutionResult
from dagster.core.instance import DagsterInstance
from dagster.core.test_utils import instance_for_test, step_output_event_filter
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
    check.invariant(not args, "There should be no positional args")
    return list(kwargs.values())[0]


def create_dep_input_fn(name):
    return lambda context, arg_dict: {name: "input_set"}


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
        result.append({context.solid.name: "compute_called"})
        return result

    return compute


def _do_construct(solids, dependencies):
    pipeline_def = PipelineDefinition(name="test", solid_defs=solids, dependencies=dependencies)
    solids = {
        s.name: Solid(name=s.name, definition=s, graph_definition=pipeline_def) for s in solids
    }
    dependency_structure = DependencyStructure.from_definitions(solids, dependencies)
    return _create_adjacency_lists(list(solids.values()), dependency_structure)


def test_empty_adjaceny_lists():
    solids = [create_root_solid("a_node")]
    forward_edges, backwards_edges = _do_construct(solids, {})
    assert forward_edges == {"a_node": set()}
    assert backwards_edges == {"a_node": set()}


def test_single_dep_adjacency_lists():
    # A <-- B
    node_a = create_root_solid("A")
    node_b = create_solid_with_deps("B", node_a)

    forward_edges, backwards_edges = _do_construct(
        [node_a, node_b], {"B": {"A": DependencyDefinition("A")}}
    )

    assert forward_edges == {"A": {"B"}, "B": set()}
    assert backwards_edges == {"B": {"A"}, "A": set()}


def test_diamond_deps_adjaceny_lists():
    forward_edges, backwards_edges = _do_construct(create_diamond_solids(), diamond_deps())

    assert forward_edges == {"A_source": {"A"}, "A": {"B", "C"}, "B": {"D"}, "C": {"D"}, "D": set()}
    assert backwards_edges == {
        "D": {"B", "C"},
        "B": {"A"},
        "C": {"A"},
        "A": {"A_source"},
        "A_source": set(),
    }


def diamond_deps():
    return {
        "A": {"A_input": DependencyDefinition("A_source")},
        "B": {"A": DependencyDefinition("A")},
        "C": {"A": DependencyDefinition("A")},
        "D": {"B": DependencyDefinition("B"), "C": DependencyDefinition("C")},
    }


def test_disconnected_graphs_adjaceny_lists():
    # A <-- B
    # C <-- D
    node_a = create_root_solid("A")
    node_b = create_solid_with_deps("B", node_a)

    node_c = create_root_solid("C")
    node_d = create_solid_with_deps("D", node_c)

    forward_edges, backwards_edges = _do_construct(
        [node_a, node_b, node_c, node_d],
        {"B": {"A": DependencyDefinition("A")}, "D": {"C": DependencyDefinition("C")}},
    )
    assert forward_edges == {"A": {"B"}, "B": set(), "C": {"D"}, "D": set()}
    assert backwards_edges == {"B": {"A"}, "A": set(), "D": {"C"}, "C": set()}


def create_diamond_solids():
    a_source = define_stub_solid("A_source", [input_set("A_input")])
    node_a = create_root_solid("A")
    node_b = create_solid_with_deps("B", node_a)
    node_c = create_solid_with_deps("C", node_a)
    node_d = create_solid_with_deps("D", node_b, node_c)
    return [node_d, node_c, node_b, node_a, a_source]


def create_diamond_pipeline():
    return PipelineDefinition(
        name="diamond_pipeline", solid_defs=create_diamond_solids(), dependencies=diamond_deps()
    )


def test_diamond_toposort():
    assert [s.name for s in create_diamond_pipeline().solids_in_topological_order] == [
        "A_source",
        "A",
        "B",
        "C",
        "D",
    ]


def test_external_diamond_toposort():
    with location_origin_from_python_file(
        python_file=__file__,
        attribute="create_diamond_pipeline",
        working_directory=None,
    ).create_handle() as handle:
        repo_location = handle.create_location()
        external_repo = next(iter(repo_location.get_repositories().values()))
        external_pipeline = next(iter(external_repo.get_all_external_pipelines()))
        assert external_pipeline.solid_names_in_topological_order == [
            "A_source",
            "A",
            "B",
            "C",
            "D",
        ]


def compute_called(name):
    return {name: "compute_called"}


def assert_equivalent_results(left, right):
    check.inst_param(left, "left", SolidExecutionResult)
    check.inst_param(right, "right", SolidExecutionResult)

    assert left.success == right.success
    assert left.name == right.name
    assert left.solid.name == right.solid.name
    assert left.output_value() == right.output_value()


def assert_all_results_equivalent(expected_results, result_results):
    check.list_param(expected_results, "expected_results", of_type=SolidExecutionResult)
    check.list_param(result_results, "result_results", of_type=SolidExecutionResult)
    assert len(expected_results) == len(result_results)
    for expected, result in zip(expected_results, result_results):
        assert_equivalent_results(expected, result)


def test_pipeline_execution_graph_diamond():
    pipe = PipelineDefinition(solid_defs=create_diamond_solids(), dependencies=diamond_deps())
    return _do_test(pipe)


def test_execute_solid_in_diamond():
    solid_result = execute_solid_within_pipeline(
        create_diamond_pipeline(), "A", inputs={"A_input": [{"a key": "a value"}]}
    )

    assert solid_result.success
    assert solid_result.output_value() == [{"a key": "a value"}, {"A": "compute_called"}]


def test_execute_aliased_solid_in_diamond():
    a_source = define_stub_solid("A_source", [input_set("A_input")])

    @pipeline
    def aliased_pipeline():
        create_root_solid("A").alias("aliased")(a_source())

    solid_result = execute_solid_within_pipeline(
        aliased_pipeline, "aliased", inputs={"A_input": [{"a key": "a value"}]}
    )

    assert solid_result.success
    assert solid_result.output_value() == [{"a key": "a value"}, {"aliased": "compute_called"}]


def test_create_pipeline_with_empty_solids_list():
    @pipeline
    def empty_pipe():
        pass

    assert execute_pipeline(empty_pipe).success


def test_singleton_pipeline():
    stub_solid = define_stub_solid("stub", [{"a key": "a value"}])

    @pipeline
    def single_solid_pipeline():
        stub_solid()

    assert execute_pipeline(single_solid_pipeline).success


def test_two_root_solid_pipeline_with_empty_dependency_definition():
    stub_solid_a = define_stub_solid("stub_a", [{"a key": "a value"}])
    stub_solid_b = define_stub_solid("stub_b", [{"a key": "a value"}])

    @pipeline
    def pipe():
        stub_solid_a()
        stub_solid_b()

    assert execute_pipeline(pipe).success


def test_two_root_solid_pipeline_with_partial_dependency_definition():
    stub_solid_a = define_stub_solid("stub_a", [{"a key": "a value"}])
    stub_solid_b = define_stub_solid("stub_b", [{"a key": "a value"}])

    single_dep_pipe = PipelineDefinition(
        solid_defs=[stub_solid_a, stub_solid_b], dependencies={"stub_a": {}}
    )

    assert execute_pipeline(single_dep_pipe).success


def _do_test(pipe):
    result = execute_pipeline(pipe)

    assert result.result_for_solid("A").output_value() == [
        input_set("A_input"),
        compute_called("A"),
    ]

    assert result.result_for_solid("B").output_value() == [
        input_set("A_input"),
        compute_called("A"),
        compute_called("B"),
    ]

    assert result.result_for_solid("C").output_value() == [
        input_set("A_input"),
        compute_called("A"),
        compute_called("C"),
    ]

    assert result.result_for_solid("D").output_value() == [
        input_set("A_input"),
        compute_called("A"),
        compute_called("C"),
        compute_called("B"),
        compute_called("D"),
    ] or result.result_for_solid("D").output_value() == [
        input_set("A_input"),
        compute_called("A"),
        compute_called("B"),
        compute_called("C"),
        compute_called("D"),
    ]


def test_empty_pipeline_execution():
    result = execute_pipeline(PipelineDefinition(solid_defs=[]))

    assert result.success


def test_pipeline_name_threaded_through_context():
    name = "foobar"

    @solid()
    def assert_name_solid(context):
        assert context.pipeline_name == name

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
        dependencies={"add_one": {"num": DependencyDefinition("return_one")}},
    )

    pipeline_result = execute_pipeline(pipeline_def)
    assert pipeline_result.success
    assert pipeline_result.result_for_solid("add_one").output_value() == 2

    env_config = {"solids": {"add_one": {"inputs": {"num": {"value": 3}}}}}

    subset_result = execute_pipeline(
        pipeline_def.get_pipeline_subset_def({"add_one"}), run_config=env_config
    )

    assert subset_result.success
    assert len(subset_result.solid_result_list) == 1
    assert subset_result.result_for_solid("add_one").output_value() == 4


def test_pipeline_explicit_subset():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid
    def add_one(num):
        return num + 1

    pipeline_def = PipelineDefinition(
        solid_defs=[return_one, add_one],
        dependencies={"add_one": {"num": DependencyDefinition("return_one")}},
    )

    pipeline_result = execute_pipeline(pipeline_def)
    assert pipeline_result.success
    assert pipeline_result.result_for_solid("add_one").output_value() == 2

    env_config = {"solids": {"add_one": {"inputs": {"num": {"value": 3}}}}}

    subset_result = execute_pipeline(
        pipeline_def, run_config=env_config, solid_selection=["add_one"]
    )

    assert subset_result.success
    assert len(subset_result.solid_result_list) == 1
    assert subset_result.result_for_solid("add_one").output_value() == 4


def test_pipeline_subset_of_subset():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid
    def add_one(num):
        return num + 1

    @pipeline
    def pipeline_def():
        add_one.alias("add_one_a")(return_one.alias("return_one_a")())
        add_one.alias("add_one_b")(return_one.alias("return_one_b")())

    pipeline_result = execute_pipeline(pipeline_def)
    assert pipeline_result.success
    assert len(pipeline_result.solid_result_list) == 4
    assert pipeline_result.result_for_solid("add_one_a").output_value() == 2

    subset_pipeline = pipeline_def.get_pipeline_subset_def({"add_one_a", "return_one_a"})
    subset_result = execute_pipeline(subset_pipeline)
    assert subset_result.success
    assert len(subset_result.solid_result_list) == 2
    assert subset_result.result_for_solid("add_one_a").output_value() == 2

    with pytest.raises(
        DagsterInvariantViolationError, match="Pipeline subsets may not be subset again."
    ):
        subset_pipeline.get_pipeline_subset_def({"add_one_a"})

    with pytest.raises(
        DagsterInvariantViolationError, match="Pipeline subsets may not be subset again."
    ):
        subset_pipeline.get_pipeline_subset_def({"add_one_a", "return_one_a"})


def test_pipeline_subset_with_multi_dependency():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid
    def return_two():
        return 2

    @lambda_solid(input_defs=[InputDefinition("dep", Nothing)])
    def noop():
        return 3

    pipeline_def = PipelineDefinition(
        solid_defs=[return_one, return_two, noop],
        dependencies={
            "noop": {
                "dep": MultiDependencyDefinition(
                    [DependencyDefinition("return_one"), DependencyDefinition("return_two")]
                )
            }
        },
    )

    pipeline_result = execute_pipeline(pipeline_def)
    assert pipeline_result.success
    assert pipeline_result.result_for_solid("noop").output_value() == 3

    subset_result = execute_pipeline(pipeline_def.get_pipeline_subset_def({"noop"}))

    assert subset_result.success
    assert len(subset_result.solid_result_list) == 1
    assert pipeline_result.result_for_solid("noop").output_value() == 3

    subset_result = execute_pipeline(
        pipeline_def.get_pipeline_subset_def({"return_one", "return_two", "noop"})
    )

    assert subset_result.success
    assert len(subset_result.solid_result_list) == 3
    assert pipeline_result.result_for_solid("noop").output_value() == 3


def test_pipeline_explicit_subset_with_multi_dependency():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid
    def return_two():
        return 2

    @lambda_solid(input_defs=[InputDefinition("dep", Nothing)])
    def noop():
        return 3

    pipeline_def = PipelineDefinition(
        solid_defs=[return_one, return_two, noop],
        dependencies={
            "noop": {
                "dep": MultiDependencyDefinition(
                    [DependencyDefinition("return_one"), DependencyDefinition("return_two")]
                )
            }
        },
    )

    pipeline_result = execute_pipeline(pipeline_def)
    assert pipeline_result.success
    assert pipeline_result.result_for_solid("noop").output_value() == 3

    subset_result = execute_pipeline(pipeline_def, solid_selection=["noop"])

    assert subset_result.success
    assert len(subset_result.solid_result_list) == 1
    assert pipeline_result.result_for_solid("noop").output_value() == 3

    subset_result = execute_pipeline(
        pipeline_def, solid_selection=["return_one", "return_two", "noop"]
    )

    assert subset_result.success
    assert len(subset_result.solid_result_list) == 3
    assert pipeline_result.result_for_solid("noop").output_value() == 3


def define_three_part_pipeline():
    @lambda_solid(input_defs=[InputDefinition("num", Int)], output_def=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    @lambda_solid(input_defs=[InputDefinition("num", Int)], output_def=OutputDefinition(Int))
    def add_two(num):
        return num + 2

    @lambda_solid(input_defs=[InputDefinition("num", Int)], output_def=OutputDefinition(Int))
    def add_three(num):
        return num + 3

    return PipelineDefinition(name="three_part_pipeline", solid_defs=[add_one, add_two, add_three])


def define_created_disjoint_three_part_pipeline():
    return define_three_part_pipeline().get_pipeline_subset_def({"add_one", "add_three"})


def test_pipeline_disjoint_subset():
    disjoint_pipeline = define_three_part_pipeline().get_pipeline_subset_def(
        {"add_one", "add_three"}
    )
    assert len(disjoint_pipeline.solids) == 2


def test_pipeline_execution_explicit_disjoint_subset():
    env_config = {
        "solids": {
            "add_one": {"inputs": {"num": {"value": 2}}},
            "add_three": {"inputs": {"num": {"value": 5}}},
        },
        "loggers": {"console": {"config": {"log_level": "ERROR"}}},
    }

    pipeline_def = define_created_disjoint_three_part_pipeline()

    result = execute_pipeline(
        pipeline_def, solid_selection=["add_one", "add_three"], run_config=env_config
    )

    assert result.success
    assert len(result.solid_result_list) == 2
    assert result.result_for_solid("add_one").output_value() == 3
    assert result.result_for_solid("add_three").output_value() == 8


def test_pipeline_wrapping_types():
    @lambda_solid(
        input_defs=[InputDefinition("value", Optional[List[Optional[String]]])],
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
        run_config={"solids": {"double_string_for_all": {"inputs": {"value": None}}}},
    ).success

    assert execute_pipeline(
        wrapping_test,
        run_config={"solids": {"double_string_for_all": {"inputs": {"value": []}}}},
    ).success

    assert execute_pipeline(
        wrapping_test,
        run_config={"solids": {"double_string_for_all": {"inputs": {"value": [{"value": "foo"}]}}}},
    ).success

    assert execute_pipeline(
        wrapping_test,
        run_config={
            "solids": {"double_string_for_all": {"inputs": {"value": [{"value": "bar"}, None]}}}
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

    @solid(output_defs=[OutputDefinition(Int, "one"), OutputDefinition(Int, "two")])
    def push_one_two(_context):
        events.append(1)
        yield Output(1, "one")
        events.append(2)
        yield Output(2, "two")

    @pipeline
    def test_streaming_iterator_multiple_outputs():
        push_one_two()

    step_event_iterator = step_output_event_filter(
        execute_pipeline_iterator(test_streaming_iterator_multiple_outputs)
    )

    one_output_step_event = next(step_event_iterator)
    assert one_output_step_event.is_successful_output
    assert one_output_step_event.step_output_data.output_name == "one"
    assert events == [1]

    two_output_step_event = next(step_event_iterator)
    assert two_output_step_event.is_successful_output
    assert two_output_step_event.step_output_data.output_name == "two"
    assert events == [1, 2]


def test_pipeline_init_failure():
    @solid(required_resource_keys={"failing"})
    def stub_solid(_):
        return None

    env_config = {}

    def failing_resource_fn(*args, **kwargs):
        raise Exception()

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={"failing": ResourceDefinition(resource_fn=failing_resource_fn)}
            )
        ]
    )
    def failing_init_pipeline():
        stub_solid()

    mem_instance = DagsterInstance.ephemeral()
    result = execute_pipeline(
        failing_init_pipeline,
        run_config=dict(env_config),
        raise_on_error=False,
        instance=mem_instance,
    )

    assert result.success is False
    event = result.event_list[-1]
    assert event.event_type_value == "PIPELINE_INIT_FAILURE"
    assert event.pipeline_init_failure_data
    assert mem_instance.get_run_by_id(result.run_id).is_failure

    with instance_for_test() as fs_instance:
        result = execute_pipeline(
            failing_init_pipeline,
            run_config=dict(env_config),
            raise_on_error=False,
            instance=fs_instance,
        )
        assert result.success is False
        event = result.event_list[-1]
        assert event.event_type_value == "PIPELINE_INIT_FAILURE"
        assert event.pipeline_init_failure_data
        assert fs_instance.get_run_by_id(result.run_id).is_failure


def test_reexecution_fs_storage():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid
    def add_one(num):
        return num + 1

    pipeline_def = PipelineDefinition(
        solid_defs=[return_one, add_one],
        dependencies={"add_one": {"num": DependencyDefinition("return_one")}},
    )
    run_config = {"storage": {"filesystem": {}}}
    instance = DagsterInstance.ephemeral()
    pipeline_result = execute_pipeline(
        pipeline_def, run_config={"storage": {"filesystem": {}}}, instance=instance
    )
    assert pipeline_result.success
    assert pipeline_result.result_for_solid("add_one").output_value() == 2

    reexecution_result = reexecute_pipeline(
        pipeline_def,
        pipeline_result.run_id,
        run_config=run_config,
        instance=instance,
    )

    assert reexecution_result.success
    assert len(reexecution_result.solid_result_list) == 2
    assert reexecution_result.result_for_solid("return_one").output_value() == 1
    assert reexecution_result.result_for_solid("add_one").output_value() == 2
    reexecution_run = instance.get_run_by_id(reexecution_result.run_id)
    assert reexecution_run.parent_run_id == pipeline_result.run_id
    assert reexecution_run.root_run_id == pipeline_result.run_id

    grandchild_result = reexecute_pipeline(
        pipeline_def,
        reexecution_result.run_id,
        run_config=run_config,
        instance=instance,
    )

    assert grandchild_result.success
    assert len(grandchild_result.solid_result_list) == 2
    assert grandchild_result.result_for_solid("return_one").output_value() == 1
    assert grandchild_result.result_for_solid("add_one").output_value() == 2
    grandchild_run = instance.get_run_by_id(grandchild_result.run_id)
    assert grandchild_run.parent_run_id == reexecution_result.run_id
    assert grandchild_run.root_run_id == pipeline_result.run_id


def test_reexecution_fs_storage_with_solid_selection():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid
    def add_one(num):
        return num + 1

    pipeline_def = PipelineDefinition(
        solid_defs=[return_one, add_one],
        dependencies={"add_one": {"num": DependencyDefinition("return_one")}},
    )
    run_config = {"storage": {"filesystem": {}}}
    instance = DagsterInstance.ephemeral()
    # Case 1: re-execute a part of a pipeline when the original pipeline doesn't have solid selection
    pipeline_result = execute_pipeline(pipeline_def, run_config, instance=instance)
    assert pipeline_result.success
    assert pipeline_result.result_for_solid("add_one").output_value() == 2

    # This is how this is actually done in dagster_graphql.implementation.pipeline_execution_manager
    reexecution_result_no_solid_selection = reexecute_pipeline(
        pipeline_def,
        parent_run_id=pipeline_result.run_id,
        run_config=run_config,
        step_selection=["return_one"],
        instance=instance,
    )
    assert reexecution_result_no_solid_selection.success
    assert len(reexecution_result_no_solid_selection.solid_result_list) == 2
    assert reexecution_result_no_solid_selection.result_for_solid("add_one").skipped
    assert reexecution_result_no_solid_selection.result_for_solid("return_one").output_value() == 1

    # Case 2: re-execute a pipeline when the original pipeline has solid selection
    pipeline_result_solid_selection = execute_pipeline(
        pipeline_def,
        run_config=run_config,
        instance=instance,
        solid_selection=["return_one"],
    )
    assert pipeline_result_solid_selection.success
    assert len(pipeline_result_solid_selection.solid_result_list) == 1
    with pytest.raises(DagsterInvariantViolationError):
        pipeline_result_solid_selection.result_for_solid("add_one")
    assert pipeline_result_solid_selection.result_for_solid("return_one").output_value() == 1

    reexecution_result_solid_selection = reexecute_pipeline(
        pipeline_def,
        parent_run_id=pipeline_result_solid_selection.run_id,
        run_config=run_config,
        instance=instance,
    )

    assert reexecution_result_solid_selection.success
    assert len(reexecution_result_solid_selection.solid_result_list) == 1
    with pytest.raises(DagsterInvariantViolationError):
        pipeline_result_solid_selection.result_for_solid("add_one")
    assert reexecution_result_solid_selection.result_for_solid("return_one").output_value() == 1

    # Case 3: re-execute a pipeline partially when the original pipeline has solid selection and
    #   re-exeucte a step which hasn't been included in the original pipeline
    with pytest.raises(
        DagsterExecutionStepNotFoundError,
        match="Can not build subset plan from unknown step: add_one",
    ):
        reexecute_pipeline(
            pipeline_def,
            parent_run_id=pipeline_result_solid_selection.run_id,
            run_config=run_config,
            step_selection=["add_one"],
            instance=instance,
        )

    # Case 4: re-execute a pipeline partially when the original pipeline has solid selection and
    #   re-exeucte a step which has been included in the original pipeline
    re_reexecution_result = reexecute_pipeline(
        pipeline_def,
        parent_run_id=reexecution_result_solid_selection.run_id,
        run_config=run_config,
        instance=instance,
        step_selection=["return_one"],
    )

    assert re_reexecution_result.success
    assert len(re_reexecution_result.solid_result_list) == 1
    assert re_reexecution_result.result_for_solid("return_one").output_value() == 1


def test_single_step_reexecution():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid
    def add_one(num):
        return num + 1

    pipeline_def = PipelineDefinition(
        solid_defs=[return_one, add_one],
        dependencies={"add_one": {"num": DependencyDefinition("return_one")}},
    )
    run_config = {"storage": {"filesystem": {}}}
    instance = DagsterInstance.ephemeral()
    pipeline_result = execute_pipeline(pipeline_def, run_config, instance=instance)
    assert pipeline_result.success
    assert pipeline_result.result_for_solid("add_one").output_value() == 2

    # This is how this is actually done in dagster_graphql.implementation.pipeline_execution_manager
    reexecution_result = reexecute_pipeline(
        pipeline_def,
        parent_run_id=pipeline_result.run_id,
        run_config=run_config,
        instance=instance,
        step_selection=["add_one"],
    )

    assert reexecution_result.success
    assert reexecution_result.result_for_solid("return_one").output_value() == None
    assert reexecution_result.result_for_solid("add_one").output_value() == 2


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
    run_config = {"storage": {"filesystem": {}}}
    pipeline_result = execute_pipeline(two_step_reexec, run_config=run_config, instance=instance)
    assert pipeline_result.success
    assert pipeline_result.result_for_solid("add_one_2").output_value() == 3

    reexecution_result = reexecute_pipeline(
        two_step_reexec,
        parent_run_id=pipeline_result.run_id,
        run_config=run_config,
        instance=instance,
        step_selection=["add_one", "add_one_2"],
    )
    assert reexecution_result.success
    assert reexecution_result.result_for_solid("return_one").output_value() == None
    assert reexecution_result.result_for_solid("add_one_2").output_value() == 3


def test_optional():
    @solid(output_defs=[OutputDefinition(Int, "x"), OutputDefinition(Int, "y", is_required=False)])
    def return_optional(_context):
        yield Output(1, "x")

    @lambda_solid
    def echo(x):
        return x

    @pipeline
    def opt_pipeline():
        x, y = return_optional()
        echo.alias("echo_x")(x)
        echo.alias("echo_y")(y)

    pipeline_result = execute_pipeline(opt_pipeline)
    assert pipeline_result.success

    result_required = pipeline_result.result_for_solid("echo_x")
    assert result_required.success

    result_optional = pipeline_result.result_for_solid("echo_y")
    assert not result_optional.success
    assert result_optional.skipped


def test_selector_with_partial_dependency_dict():
    executed = {}

    @solid
    def def_one(_):
        executed["one"] = True

    @solid
    def def_two(_):
        executed["two"] = True

    pipe_two = PipelineDefinition(
        name="pipe_two", solid_defs=[def_one, def_two], dependencies={"def_one": {}}
    )

    execute_pipeline(pipe_two)

    # if it is in solid defs it will execute even if it is not in dependencies dictionary
    assert set(executed.keys()) == {"one", "two"}


def test_selector_with_subset_for_execution():
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

    assert pipe.get_pipeline_subset_def({"def_two"}).solids_to_execute == {"def_two"}


def test_default_run_id():
    called = {}

    @solid
    def check_run_id(context):
        called["yes"] = True
        assert uuid.UUID(context.run_id)
        called["run_id"] = context.run_id

    pipeline_def = PipelineDefinition(solid_defs=[check_run_id])

    result = execute_pipeline(pipeline_def)
    assert result.run_id == called["run_id"]
    assert called["yes"]


def test_pipeline_tags():
    called = {}

    @solid
    def check_tags(context):
        assert context.get_tag("foo") == "bar"
        called["yup"] = True

    pipeline_def_with_tags = PipelineDefinition(
        name="injected_run_id", solid_defs=[check_tags], tags={"foo": "bar"}
    )
    result = execute_pipeline(pipeline_def_with_tags)
    assert result.success
    assert called["yup"]

    called = {}
    pipeline_def_with_override_tags = PipelineDefinition(
        name="injected_run_id", solid_defs=[check_tags], tags={"foo": "notbar"}
    )
    result = execute_pipeline(pipeline_def_with_override_tags, tags={"foo": "bar"})
    assert result.success
    assert called["yup"]


def test_multi_dep_optional():
    @lambda_solid
    def ret_one():
        return 1

    @lambda_solid
    def echo(x):
        return x

    @solid(output_defs=[OutputDefinition(name="skip", is_required=False)])
    def skip(_):
        return
        yield  # pylint: disable=unreachable

    @solid
    def collect(_, items):
        return items

    @solid
    def collect_and(_, items, other):
        return items + [other]

    @pipeline
    def test_remaining():
        collect([ret_one(), skip()])

    result = execute_pipeline(test_remaining)
    assert result.success
    assert result.result_for_solid("collect").output_value() == [1]

    @pipeline
    def test_all_skip():
        collect([skip(), skip(), skip()])

    result = execute_pipeline(test_all_skip)
    assert result.success
    assert result.result_for_solid("collect").skipped

    @pipeline
    def test_skipped_upstream():
        collect([ret_one(), echo(echo(skip()))])

    result = execute_pipeline(test_skipped_upstream)
    assert result.success
    assert result.result_for_solid("collect").output_value() == [1]

    @pipeline
    def test_all_upstream_skip():
        collect([echo(skip()), echo(skip()), echo(skip())])

    result = execute_pipeline(test_all_upstream_skip)
    assert result.success
    assert result.result_for_solid("collect").skipped

    @pipeline
    def test_all_upstream_skip_with_other():
        collect_and([echo(skip()), echo(skip()), echo(skip())], ret_one())

    result = execute_pipeline(test_all_upstream_skip_with_other)
    assert result.success
    assert result.result_for_solid("collect_and").skipped

    @pipeline
    def test_all_skip_with_other():
        collect_and([skip(), skip(), skip()], ret_one())

    result = execute_pipeline(test_all_skip_with_other)
    assert result.success
    assert result.result_for_solid("collect_and").skipped

    @pipeline
    def test_other_skip():
        collect_and([ret_one(), skip(), skip()], skip())

    result = execute_pipeline(test_other_skip)
    assert result.success
    assert result.result_for_solid("collect_and").skipped

    @pipeline
    def test_other_skip_upstream():
        collect_and([ret_one(), skip(), skip()], echo(skip()))

    result = execute_pipeline(test_other_skip_upstream)
    assert result.success
    assert result.result_for_solid("collect_and").skipped
