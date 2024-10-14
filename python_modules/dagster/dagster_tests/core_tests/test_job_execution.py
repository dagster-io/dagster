import uuid
import warnings
from typing import Mapping, Sequence, Set, Tuple

import pytest
from dagster import (
    DependencyDefinition,
    Field,
    GraphDefinition,
    In,
    Int,
    List,
    MultiDependencyDefinition,
    Nothing,
    Optional,
    Out,
    Output,
    ResourceDefinition,
    String,
    _check as check,
    job,
    op,
    reconstructable,
)
from dagster._core.definitions.dependency import DependencyMapping, DependencyStructure, OpNode
from dagster._core.definitions.graph_definition import create_adjacency_lists
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.errors import DagsterExecutionStepNotFoundError, DagsterInvariantViolationError
from dagster._core.execution.api import ReexecutionOptions, execute_job
from dagster._core.instance import DagsterInstance
from dagster._core.test_utils import instance_for_test
from dagster._core.utility_ops import create_op_with_deps, create_root_op, create_stub_op, input_set
from dagster._core.workspace.load import location_origin_from_python_file

# protected members
# pylint: disable=W0212


def _default_passthrough_compute_fn(*args, **kwargs):
    check.invariant(not args, "There should be no positional args")
    return next(iter(kwargs.values()))


def create_dep_input_fn(name):
    return lambda context, arg_dict: {name: "input_set"}


def make_compute_fn():
    def compute(context, inputs):
        passed_rows = []
        seen = set()
        for row in inputs.values():
            for item in row:
                key = next(iter(item.keys()))
                if key not in seen:
                    seen.add(key)
                    passed_rows.append(item)

        result = []
        result.extend(passed_rows)
        result.append({context.op.name: "compute_called"})
        return result

    return compute


def _do_construct(
    ops: Sequence[OpDefinition],
    dependencies: DependencyMapping[str],
) -> Tuple[Mapping[str, Set[str]], Mapping[str, Set[str]]]:
    job_def = JobDefinition(
        graph_def=GraphDefinition(name="test", node_defs=ops, dependencies=dependencies)
    )
    op_map = {
        s.name: OpNode(name=s.name, definition=s, graph_definition=job_def.graph) for s in ops
    }
    dependency_structure = DependencyStructure.from_definitions(op_map, dependencies)
    return create_adjacency_lists(list(op_map.values()), dependency_structure)


def test_empty_adjacency_lists():
    ops = [create_root_op("a_node")]
    forward_edges, backwards_edges = _do_construct(ops, {})
    assert forward_edges == {"a_node": set()}
    assert backwards_edges == {"a_node": set()}


def test_single_dep_adjacency_lists():
    # A <-- B
    node_a = create_root_op("A")
    node_b = create_op_with_deps("B", node_a)

    forward_edges, backwards_edges = _do_construct(
        [node_a, node_b], {"B": {"A": DependencyDefinition("A")}}
    )

    assert forward_edges == {"A": {"B"}, "B": set()}
    assert backwards_edges == {"B": {"A"}, "A": set()}


def test_diamond_deps_adjaceny_lists():
    forward_edges, backwards_edges = _do_construct(create_diamond_ops(), diamond_deps())

    assert forward_edges == {
        "A_source": {"A"},
        "A": {"B", "C"},
        "B": {"D"},
        "C": {"D"},
        "D": set(),
    }
    assert backwards_edges == {
        "D": {"B", "C"},
        "B": {"A"},
        "C": {"A"},
        "A": {"A_source"},
        "A_source": set(),
    }


def diamond_deps() -> Mapping[str, Mapping[str, DependencyDefinition]]:
    return {
        "A": {"A_input": DependencyDefinition("A_source")},
        "B": {"A": DependencyDefinition("A")},
        "C": {"A": DependencyDefinition("A")},
        "D": {"B": DependencyDefinition("B"), "C": DependencyDefinition("C")},
    }


def test_disconnected_graphs_adjaceny_lists():
    # A <-- B
    # C <-- D
    node_a = create_root_op("A")
    node_b = create_op_with_deps("B", node_a)

    node_c = create_root_op("C")
    node_d = create_op_with_deps("D", node_c)

    forward_edges, backwards_edges = _do_construct(
        [node_a, node_b, node_c, node_d],
        {"B": {"A": DependencyDefinition("A")}, "D": {"C": DependencyDefinition("C")}},
    )
    assert forward_edges == {"A": {"B"}, "B": set(), "C": {"D"}, "D": set()}
    assert backwards_edges == {"B": {"A"}, "A": set(), "D": {"C"}, "C": set()}


def create_diamond_ops():
    a_source = create_stub_op("A_source", [input_set("A_input")])
    node_a = create_root_op("A")
    node_b = create_op_with_deps("B", node_a)
    node_c = create_op_with_deps("C", node_a)
    node_d = create_op_with_deps("D", node_b, node_c)
    return [node_d, node_c, node_b, node_a, a_source]


def create_diamond_job():
    return GraphDefinition(
        name="diamond_graph",
        node_defs=create_diamond_ops(),
        dependencies=diamond_deps(),
    ).to_job()


def test_diamond_toposort():
    assert [s.name for s in create_diamond_job().graph.nodes_in_topological_order] == [
        "A_source",
        "A",
        "B",
        "C",
        "D",
    ]


def test_external_diamond_toposort():
    with instance_for_test() as instance:
        with location_origin_from_python_file(
            python_file=__file__,
            attribute="create_diamond_job",
            working_directory=None,
        ).create_single_location(instance) as repo_location:
            external_repo = next(iter(repo_location.get_repositories().values()))
            remote_job = next(iter(external_repo.get_all_jobs()))
            assert remote_job.node_names_in_topological_order == [
                "A_source",
                "A",
                "B",
                "C",
                "D",
            ]


def compute_called(name: str) -> Mapping[str, object]:
    return {name: "compute_called"}


def test_job_execution_graph_diamond():
    pipe = GraphDefinition(
        node_defs=create_diamond_ops(), name="test", dependencies=diamond_deps()
    ).to_job()
    return _do_test(pipe)


def test_execute_op_in_diamond():
    op_result = create_diamond_job().execute_in_process(
        op_selection=["A"],
        run_config={"ops": {"A": {"inputs": {"A_input": {"value": [{"a key": "a value"}]}}}}},
    )

    assert op_result.success
    assert op_result.output_for_node("A") == [
        {"a key": "a value"},
        {"A": "compute_called"},
    ]


def test_execute_aliased_op_in_diamond():
    a_source = create_stub_op("A_source", [input_set("A_input")])

    @job
    def aliased_job():
        create_root_op("A").alias("aliased")(a_source())

    result = aliased_job.execute_in_process(
        op_selection=["aliased"],
        run_config={"ops": {"aliased": {"inputs": {"A_input": {"value": [{"a key": "a value"}]}}}}},
    )

    assert result.success
    assert result.output_for_node("aliased") == [
        {"a key": "a value"},
        {"aliased": "compute_called"},
    ]


def test_create_job_with_empty_ops_list():
    @job
    def empty_pipe():
        pass

    assert empty_pipe.execute_in_process().success


def test_singleton_job():
    stub_op = create_stub_op("stub", [{"a key": "a value"}])

    # will fail if any warning is emitted
    with warnings.catch_warnings():
        warnings.simplefilter("error")

        @job
        def single_op_job():
            stub_op()

        assert single_op_job.execute_in_process().success


def test_two_root_op_job_with_empty_dependency_definition():
    stub_op_a = create_stub_op("stub_a", [{"a key": "a value"}])
    stub_op_b = create_stub_op("stub_b", [{"a key": "a value"}])

    @job
    def pipe():
        stub_op_a()
        stub_op_b()

    assert pipe.execute_in_process().success


def test_two_root_op_job_with_partial_dependency_definition():
    stub_op_a = create_stub_op("stub_a", [{"a key": "a value"}])
    stub_op_b = create_stub_op("stub_b", [{"a key": "a value"}])

    single_dep_pipe = GraphDefinition(
        node_defs=[stub_op_a, stub_op_b],
        name="test",
        dependencies={"stub_a": {}},
    ).to_job()

    assert single_dep_pipe.execute_in_process().success


def _do_test(the_job):
    result = the_job.execute_in_process()

    assert result.output_for_node("A") == [
        input_set("A_input"),
        compute_called("A"),
    ]

    assert result.output_for_node("B") == [
        input_set("A_input"),
        compute_called("A"),
        compute_called("B"),
    ]

    assert result.output_for_node("C") == [
        input_set("A_input"),
        compute_called("A"),
        compute_called("C"),
    ]

    assert result.output_for_node("D") == [
        input_set("A_input"),
        compute_called("A"),
        compute_called("C"),
        compute_called("B"),
        compute_called("D"),
    ] or result.output_for_node("D") == [
        input_set("A_input"),
        compute_called("A"),
        compute_called("B"),
        compute_called("C"),
        compute_called("D"),
    ]


def test_empty_job_execution():
    result = GraphDefinition(node_defs=[], name="test").execute_in_process()

    assert result.success


def test_job_name_threaded_through_context():
    name = "foobar"

    @op()
    def assert_name_op(context):
        assert context.job_name == name

    result = GraphDefinition(name="foobar", node_defs=[assert_name_op]).execute_in_process()

    assert result.success


def test_job_subset():
    @op
    def return_one():
        return 1

    @op
    def add_one(num):
        return num + 1

    job_def = GraphDefinition(
        node_defs=[return_one, add_one],
        name="test",
        dependencies={"add_one": {"num": DependencyDefinition("return_one")}},
    ).to_job()

    result = job_def.execute_in_process()
    assert result.success
    assert result.output_for_node("add_one") == 2

    env_config = {"ops": {"add_one": {"inputs": {"num": {"value": 3}}}}}

    subset_result = job_def.execute_in_process(run_config=env_config, op_selection=["add_one"])

    assert subset_result.success
    with pytest.raises(DagsterInvariantViolationError):
        subset_result.output_for_node("return_one")
    assert subset_result.output_for_node("add_one") == 4


def test_job_explicit_subset():
    @op
    def return_one():
        return 1

    @op
    def add_one(num):
        return num + 1

    job_def = GraphDefinition(
        node_defs=[return_one, add_one],
        name="test",
        dependencies={"add_one": {"num": DependencyDefinition("return_one")}},
    ).to_job()

    result = job_def.execute_in_process()
    assert result.success
    assert result.output_for_node("add_one") == 2

    env_config = {"ops": {"add_one": {"inputs": {"num": {"value": 3}}}}}

    subset_result = job_def.execute_in_process(run_config=env_config, op_selection=["add_one"])

    assert subset_result.success
    with pytest.raises(DagsterInvariantViolationError):
        subset_result.output_for_node("return_one")
    assert subset_result.output_for_node("add_one") == 4


def test_job_subset_of_subset():
    @op
    def return_one():
        return 1

    @op
    def add_one(num):
        return num + 1

    @job
    def job_def():
        add_one.alias("add_one_a")(return_one.alias("return_one_a")())
        add_one.alias("add_one_b")(return_one.alias("return_one_b")())

    result = job_def.execute_in_process()
    assert result.success
    assert result.output_for_node("return_one_a") == 1
    assert result.output_for_node("add_one_a") == 2
    assert result.output_for_node("return_one_b") == 1
    assert result.output_for_node("add_one_b") == 2

    subset_job = job_def.get_subset(op_selection=["add_one_a", "return_one_a"])
    subset_result = subset_job.execute_in_process()
    assert subset_result.success
    with pytest.raises(DagsterInvariantViolationError):
        subset_result.output_for_node("return_one_b")
    assert subset_result.output_for_node("return_one_a") == 1
    assert subset_result.output_for_node("add_one_a") == 2


def test_job_subset_with_multi_dependency():
    @op
    def return_one():
        return 1

    @op
    def return_two():
        return 2

    @op(ins={"dep": In(Nothing)})
    def noop():
        return 3

    job_def = GraphDefinition(
        node_defs=[return_one, return_two, noop],
        name="test",
        dependencies={
            "noop": {
                "dep": MultiDependencyDefinition(
                    [
                        DependencyDefinition("return_one"),
                        DependencyDefinition("return_two"),
                    ]
                )
            }
        },
    ).to_job()

    result = job_def.execute_in_process()
    assert result.success
    assert result.output_for_node("noop") == 3

    subset_result = job_def.get_subset(op_selection=["noop"]).execute_in_process()

    assert subset_result.success
    with pytest.raises(DagsterInvariantViolationError):
        subset_result.output_for_node("return_one")
    assert subset_result.output_for_node("noop") == 3

    subset_result = job_def.get_subset(
        op_selection=["return_one", "return_two", "noop"]
    ).execute_in_process()

    assert subset_result.success
    assert subset_result.output_for_node("return_one") == 1
    assert subset_result.output_for_node("return_two") == 2
    assert subset_result.output_for_node("noop") == 3


def test_job_explicit_subset_with_multi_dependency():
    @op
    def return_one():
        return 1

    @op
    def return_two():
        return 2

    @op(ins={"dep": In(Nothing)})
    def noop():
        return 3

    job_def = GraphDefinition(
        node_defs=[return_one, return_two, noop],
        name="test",
        dependencies={
            "noop": {
                "dep": MultiDependencyDefinition(
                    [
                        DependencyDefinition("return_one"),
                        DependencyDefinition("return_two"),
                    ]
                )
            }
        },
    ).to_job()

    job = job_def.execute_in_process()
    assert job.success
    assert job.output_for_node("noop") == 3

    subset_result = job_def.execute_in_process(op_selection=["noop"])

    assert subset_result.success
    with pytest.raises(DagsterInvariantViolationError):
        subset_result.output_for_node("return_one")
    assert job.output_for_node("noop") == 3

    subset_result = job_def.execute_in_process(op_selection=["return_one", "return_two", "noop"])

    assert subset_result.success
    assert subset_result.output_for_node("return_one") == 1
    assert subset_result.output_for_node("return_two") == 2
    assert subset_result.output_for_node("noop") == 3


def define_three_part_job():
    @op(ins={"num": In(Int)}, out=Out(Int))
    def add_one(num):
        return num + 1

    @op(ins={"num": In(Int)}, out=Out(Int))
    def add_two(num):
        return num + 2

    @op(ins={"num": In(Int)}, out=Out(Int))
    def add_three(num):
        return num + 3

    return GraphDefinition(name="three_part_job", node_defs=[add_one, add_two, add_three]).to_job()


def define_created_disjoint_three_part_job():
    return define_three_part_job().get_subset(op_selection=["add_one", "add_three"])


def test_job_disjoint_subset():
    disjoint_job = define_three_part_job().get_subset(op_selection=["add_one", "add_three"])
    assert len(disjoint_job.nodes) == 2


def test_job_execution_explicit_disjoint_subset():
    env_config = {
        "ops": {
            "add_one": {"inputs": {"num": {"value": 2}}},
            "add_three": {"inputs": {"num": {"value": 5}}},
        },
        "loggers": {"console": {"config": {"log_level": "ERROR"}}},
    }

    job_def = define_created_disjoint_three_part_job()

    result = job_def.execute_in_process(
        op_selection=["add_one", "add_three"], run_config=env_config
    )

    assert result.success
    assert result.output_for_node("add_one") == 3
    with pytest.raises(DagsterInvariantViolationError):
        result.output_for_node("add_two")
    assert result.output_for_node("add_three") == 8


def test_job_wrapping_types():
    @op(
        ins={"value": In(Optional[List[Optional[String]]])},
        out=Out(Optional[List[Optional[String]]]),
    )
    def double_string_for_all(value):
        if not value:
            return value

        output = []
        for item in value:
            output.append(None if item is None else item + item)
        return output

    @job
    def wrapping_test():
        double_string_for_all()

    assert wrapping_test.execute_in_process(
        run_config={"ops": {"double_string_for_all": {"inputs": {"value": None}}}},
    ).success

    assert wrapping_test.execute_in_process(
        run_config={"ops": {"double_string_for_all": {"inputs": {"value": []}}}},
    ).success

    assert wrapping_test.execute_in_process(
        run_config={"ops": {"double_string_for_all": {"inputs": {"value": [{"value": "foo"}]}}}},
    ).success

    assert wrapping_test.execute_in_process(
        run_config={
            "ops": {"double_string_for_all": {"inputs": {"value": [{"value": "bar"}, None]}}}
        },
    ).success


def test_job_init_failure():
    @op(required_resource_keys={"failing"})
    def stub_op(_):
        return None

    env_config = {}

    def failing_resource_fn(*args, **kwargs):
        raise Exception()

    @job(resource_defs={"failing": ResourceDefinition(resource_fn=failing_resource_fn)})
    def failing_init_job():
        stub_op()

    mem_instance = DagsterInstance.ephemeral()
    result = failing_init_job.execute_in_process(
        run_config=dict(env_config),
        raise_on_error=False,
        instance=mem_instance,
    )
    assert result.success is False
    event = result.all_events[-1]
    assert event.event_type_value == "PIPELINE_FAILURE"
    assert event.job_failure_data
    assert mem_instance.get_run_by_id(result.run_id).is_failure_or_canceled

    with instance_for_test() as fs_instance:
        result = failing_init_job.execute_in_process(
            run_config=dict(env_config),
            raise_on_error=False,
            instance=fs_instance,
        )
        assert result.success is False
        event = result.all_events[-1]
        assert event.event_type_value == "PIPELINE_FAILURE"
        assert event.job_failure_data
        assert fs_instance.get_run_by_id(result.run_id).is_failure_or_canceled


def get_retry_job() -> JobDefinition:
    @op(
        config_schema={
            "fail": Field(bool, is_required=False, default_value=False),
        },
    )
    def return_one(context):
        if context.op_config["fail"]:
            raise Exception("FAILURE")
        return 1

    @op
    def add_one(num):
        return num + 1

    return GraphDefinition(
        node_defs=[return_one, add_one],
        name="test",
        dependencies={"add_one": {"num": DependencyDefinition("return_one")}},
    ).to_job()


def test_reexecution_fs_storage():
    recon_job = reconstructable(get_retry_job)

    with instance_for_test() as instance:
        with execute_job(recon_job, instance=instance) as result:
            assert result.success
            assert result.output_for_node("add_one") == 2
            run_id = result.run_id

        with execute_job(
            recon_job,
            instance=instance,
            reexecution_options=ReexecutionOptions(parent_run_id=run_id),
        ) as child_result:
            assert child_result.success
            assert child_result.output_for_node("return_one") == 1
            assert child_result.output_for_node("add_one") == 2
            child_run = instance.get_run_by_id(child_result.run_id)
            assert child_run is not None
            assert child_run.parent_run_id == run_id
            assert child_run.root_run_id == run_id
            child_run_id = child_run.run_id

        with execute_job(
            recon_job,
            reexecution_options=ReexecutionOptions(parent_run_id=child_run_id),
            instance=instance,
        ) as grandchild_result:
            assert grandchild_result.success
            assert grandchild_result.output_for_node("return_one") == 1
            assert grandchild_result.output_for_node("add_one") == 2
            grandchild_run = instance.get_run_by_id(grandchild_result.run_id)
            assert grandchild_run is not None
            assert grandchild_run.parent_run_id == child_run_id
            assert grandchild_run.root_run_id == run_id


def test_reexecution_fs_storage_after_fail():
    recon_job = reconstructable(get_retry_job)

    with instance_for_test() as instance:
        with execute_job(
            recon_job,
            instance=instance,
            run_config={
                "ops": {"return_one": {"config": {"fail": True}}},
            },
            raise_on_error=False,
        ) as result:
            assert not result.success
            run_id = result.run_id

        with execute_job(
            recon_job,
            instance=instance,
            reexecution_options=ReexecutionOptions(parent_run_id=run_id),
            run_config={},
        ) as child_result:
            assert child_result.success
            assert child_result.output_for_node("return_one") == 1
            assert child_result.output_for_node("add_one") == 2
            child_run = instance.get_run_by_id(child_result.run_id)
            assert child_run is not None
            assert child_run.parent_run_id == result.run_id
            assert child_run.root_run_id == result.run_id
            child_run_id = child_run.run_id

        with execute_job(
            recon_job,
            reexecution_options=ReexecutionOptions(parent_run_id=child_run_id),
            instance=instance,
            run_config={},
        ) as grandchild_result:
            assert grandchild_result.success
            assert grandchild_result.output_for_node("return_one") == 1
            assert grandchild_result.output_for_node("add_one") == 2
            grandchild_run = instance.get_run_by_id(grandchild_result.run_id)
            assert grandchild_run is not None
            assert grandchild_run.parent_run_id == child_run_id
            assert grandchild_run.root_run_id == run_id


def test_reexecution_fs_storage_with_op_selection():
    recon_job = reconstructable(get_retry_job)
    with instance_for_test() as instance:
        # Case 1: re-execute a part of a job when the original job
        # doesn't have op selection.
        with execute_job(
            recon_job,
            instance=instance,
        ) as result:
            assert result.success
            run_id = result.run_id

        with execute_job(
            recon_job,
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=run_id, step_selection=["return_one"]
            ),
        ) as child_result_no_op_selection:
            assert child_result_no_op_selection.success
            assert child_result_no_op_selection.output_for_node("return_one") == 1
            with pytest.raises(DagsterInvariantViolationError):
                result.output_for_node("add_one")

        # Case 2: re-execute a job when the original job has op
        # selection
        with execute_job(
            recon_job,
            instance=instance,
            op_selection=["return_one"],
        ) as result:
            assert result.success
            assert result.output_for_node("return_one") == 1
            with pytest.raises(DagsterInvariantViolationError):
                result.output_for_node("add_one")
            op_selection_run_id = result.run_id

        with execute_job(
            recon_job,
            instance=instance,
            reexecution_options=ReexecutionOptions(parent_run_id=op_selection_run_id),
        ) as child_result_yes_op_selection:
            assert child_result_yes_op_selection.success
            assert child_result_yes_op_selection.output_for_node("return_one") == 1
            with pytest.raises(DagsterInvariantViolationError):
                result.output_for_node("add_one")

        # Case 3: re-execute a job partially when the original job has op selection and
        #   re-exeucte a step which hasn't been included in the original job
        with pytest.raises(
            DagsterExecutionStepNotFoundError,
            match="Step selection refers to unknown step: add_one",
        ):
            execute_job(
                recon_job,
                reexecution_options=ReexecutionOptions(
                    parent_run_id=op_selection_run_id, step_selection=["add_one"]
                ),
                instance=instance,
            )

        # Case 4: re-execute a job partially when the original job has op selection and
        #   re-exeucte a step which has been included in the original job
        with execute_job(
            recon_job,
            reexecution_options=ReexecutionOptions(
                parent_run_id=op_selection_run_id, step_selection=["return_one"]
            ),
            instance=instance,
        ) as result:
            assert result.success
            assert result.output_for_node("return_one") == 1


def test_single_step_reexecution():
    recon_job = reconstructable(get_retry_job)
    with instance_for_test() as instance:
        with execute_job(
            recon_job,
            instance=instance,
        ) as result:
            assert result.success
            assert result.output_for_node("add_one") == 2
            run_id = result.run_id

        with execute_job(
            recon_job,
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=run_id, step_selection=["add_one"]
            ),
        ) as child_result:
            assert child_result.success
            assert child_result.output_for_node("add_one") == 2
            with pytest.raises(DagsterInvariantViolationError):
                result.output_for_node("return_one")


def test_two_step_reexecution():
    recon_job = reconstructable(get_retry_job)
    with instance_for_test() as instance:
        with execute_job(
            recon_job,
            instance=instance,
        ) as result:
            assert result.success
            assert result.output_for_node("add_one") == 2
            run_id = result.run_id

        with execute_job(
            recon_job,
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=run_id, step_selection=["return_one", "add_one"]
            ),
        ) as child_result:
            assert child_result.success
            assert child_result.output_for_node("return_one") == 1
            assert child_result.output_for_node("add_one") == 2


def test_optional():
    @op(
        out={
            "x": Out(Int),
            "y": Out(Int, is_required=False),
        }
    )
    def return_optional(_context):
        yield Output(1, "x")

    @op
    def echo(x):
        return x

    @job
    def opt_job():
        x, y = return_optional()
        echo.alias("echo_x")(x)
        echo.alias("echo_y")(y)

    result = opt_job.execute_in_process()
    assert result.success
    assert result.is_node_success("echo_x")
    assert result.is_node_skipped("echo_y")


def test_selector_with_partial_dependency_dict():
    executed = {}

    @op
    def def_one(_):
        executed["one"] = True

    @op
    def def_two(_):
        executed["two"] = True

    pipe_two = GraphDefinition(
        name="pipe_two", node_defs=[def_one, def_two], dependencies={"def_one": {}}
    ).to_job()

    pipe_two.execute_in_process()

    # if it is in op defs it will execute even if it is not in dependencies dictionary
    assert set(executed.keys()) == {"one", "two"}


def test_selector_with_subset_for_execution():
    @op
    def def_one(_):
        pass

    @op
    def def_two(_):
        pass

    # dsl subsets the definitions appropriately
    @job
    def pipe():
        def_one()
        def_two()

    assert pipe.get_subset(op_selection=["def_two"]).op_selection_data.resolved_op_selection == {
        "def_two"
    }


def test_default_run_id():
    called = {}

    @op
    def check_run_id(context):
        called["yes"] = True
        assert uuid.UUID(context.run_id)
        called["run_id"] = context.run_id

    job_def = GraphDefinition(node_defs=[check_run_id], name="test").to_job()

    result = job_def.execute_in_process()
    assert result.run_id == called["run_id"]
    assert called["yes"]


def test_job_tags():
    called = {}

    @op
    def check_tags(context):
        assert context.get_tag("foo") == "bar"
        called["yup"] = True

    job_def_with_tags = GraphDefinition(
        name="injected_run_id", node_defs=[check_tags], tags={"foo": "bar"}
    ).to_job()
    result = job_def_with_tags.execute_in_process()
    assert result.success
    assert called["yup"]

    called = {}
    job_def_with_override_tags = GraphDefinition(
        name="injected_run_id", node_defs=[check_tags], tags={"foo": "notbar"}
    ).to_job()
    result = job_def_with_override_tags.execute_in_process(tags={"foo": "bar"})
    assert result.success
    assert called["yup"]


def test_multi_dep_optional():
    @op
    def ret_one():
        return 1

    @op
    def echo(x):
        return x

    @op(out={"skip": Out(is_required=False)})
    def skip(_):
        return
        yield  # pylint: disable=unreachable

    @op
    def collect(_, items):
        return items

    @op
    def collect_and(_, items, other):
        return items + [other]

    @job
    def test_remaining():
        collect([ret_one(), skip()])

    result = test_remaining.execute_in_process()
    assert result.success
    assert result.output_for_node("collect") == [1]

    @job
    def test_all_skip():
        collect([skip(), skip(), skip()])

    result = test_all_skip.execute_in_process()
    assert result.success
    assert result.is_node_skipped("collect")

    @job
    def test_skipped_upstream():
        collect([ret_one(), echo(echo(skip()))])

    result = test_skipped_upstream.execute_in_process()
    assert result.success
    assert result.output_for_node("collect") == [1]

    @job
    def test_all_upstream_skip():
        collect([echo(skip()), echo(skip()), echo(skip())])

    result = test_all_upstream_skip.execute_in_process()
    assert result.success
    assert result.is_node_skipped("collect")

    @job
    def test_all_upstream_skip_with_other():
        collect_and([echo(skip()), echo(skip()), echo(skip())], ret_one())

    result = test_all_upstream_skip_with_other.execute_in_process()
    assert result.success
    assert result.is_node_skipped("collect_and")

    @job
    def test_all_skip_with_other():
        collect_and([skip(), skip(), skip()], ret_one())

    result = test_all_skip_with_other.execute_in_process()
    assert result.success
    assert result.is_node_skipped("collect_and")

    @job
    def test_other_skip():
        collect_and([ret_one(), skip(), skip()], skip())

    result = test_other_skip.execute_in_process()
    assert result.success
    assert result.is_node_skipped("collect_and")

    @job
    def test_other_skip_upstream():
        collect_and([ret_one(), skip(), skip()], echo(skip()))

    result = test_other_skip_upstream.execute_in_process()
    assert result.success
    assert result.is_node_skipped("collect_and")
