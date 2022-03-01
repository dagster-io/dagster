from typing import List

import pytest

from dagster import (
    ConfigMapping,
    DynamicOut,
    DynamicOutput,
    In,
    graph,
    job,
    op,
    repository,
    root_input_manager,
)
from dagster.core.errors import DagsterInvalidSubsetError
from dagster.core.events import DagsterEventType
from dagster.core.execution.execute_in_process_result import ExecuteInProcessResult


@op
def return_one():
    return 1


@op
def return_two():
    return 2


@op
def adder(num1: int, num2: int):
    return num1 + num2


@op
def add_one(num: int):
    return num + 1


@graph
def do_it_all():
    add_one(adder(return_one(), return_two()))


def _success_step_keys(result: ExecuteInProcessResult):
    return [
        evt.step_key
        for evt in result.all_node_events
        if evt.event_type == DagsterEventType.STEP_SUCCESS
    ]


def test_repo_can_load():
    my_subset_job = do_it_all.to_job(name="subset_job", op_selection=["add_one"])

    @repository
    def my_repo():
        return [do_it_all, my_subset_job]

    assert {job.name for job in my_repo.get_all_jobs()} == {"do_it_all", "subset_job"}


def test_simple_op_selection_on_graph_def():
    result = do_it_all.execute_in_process(op_selection=["*adder"])

    assert result.success

    executed_step_keys = _success_step_keys(result)
    assert len(executed_step_keys) == 3
    assert "add_one" not in [executed_step_keys]


def test_simple_op_selection_on_job_def():
    my_subset_job = do_it_all.to_job(op_selection=["*adder"])
    result = my_subset_job.execute_in_process()

    assert result.success

    executed_step_keys = _success_step_keys(result)
    assert len(executed_step_keys) == 3
    assert "add_one" not in [executed_step_keys]


def test_select_all_on_job_def():
    my_subset_job = do_it_all.to_job(op_selection=["*"])
    result = my_subset_job.execute_in_process()

    assert result.success

    executed_step_keys = _success_step_keys(result)
    assert len(executed_step_keys) == 4


def test_simple_op_selection_on_job_execution():
    my_job = do_it_all.to_job()
    result = my_job.execute_in_process(op_selection=["*adder"])

    assert result.success

    executed_step_keys = _success_step_keys(result)
    assert len(executed_step_keys) == 3
    assert "add_one" not in [executed_step_keys]


def test_simple_op_selection_on_subset_execution():
    my_subset_job = do_it_all.to_job(op_selection=["*adder"])
    # option 1 - overwrites op_selection
    result = my_subset_job.execute_in_process(op_selection=["*"])

    assert result.success

    executed_step_keys = _success_step_keys(result)
    assert len(executed_step_keys) == 3
    assert "add_one" not in [executed_step_keys]


def test_unselected_extra_config_input():
    @op
    def root(_):
        return "public.table_1"

    @op(config_schema={"some_config": str})
    def takes_input(_, input_table):
        return input_table

    @graph
    def full():
        takes_input(root())

    # Requires passing some config to the op to bypass the op block level optionality
    run_config = {"ops": {"takes_input": {"config": {"some_config": "a"}}}}

    full_job = full.to_job()
    assert full_job.execute_in_process(run_config=run_config).success

    # Subselected job shouldn't require the unselected solid's config
    assert full_job.execute_in_process(op_selection=["root"]).success
    # Should also be able to ignore the extra input config
    assert full_job.execute_in_process(run_config=run_config, op_selection=["root"]).success


def test_unsatisfied_input_use_config():
    @op
    def start(_, x):
        return x

    @op
    def end(_, x=1):
        return x

    @graph
    def testing():
        end(start())

    full_job = testing.to_job()

    result = full_job.execute_in_process(
        run_config={"ops": {"start": {"inputs": {"x": {"value": 4}}}}}
    )
    assert result.success
    assert result.output_for_node("end") == 4

    # test to ensure that if start is not being executed its input config is still allowed (and ignored)
    subset_result = full_job.execute_in_process(
        run_config={"ops": {"start": {"inputs": {"x": {"value": 4}}}}},
        op_selection=["end"],
    )
    assert subset_result.success
    assert subset_result.output_for_node("end") == 1

    # test to ensure that if the input is connected we will use the input value provided in config
    subset_result = full_job.execute_in_process(
        run_config={"ops": {"end": {"inputs": {"x": {"value": 4}}}}},
        op_selection=["end"],
    )
    assert subset_result.success
    assert subset_result.output_for_node("end") == 4


def test_unsatisfied_input_use_root_input_manager():
    @root_input_manager(input_config_schema=int)
    def config_io_man(context):
        return context.config

    @op(ins={"x": In(root_manager_key="my_loader")})
    def start(_, x):
        return x

    @op(ins={"x": In(root_manager_key="my_loader")})
    def end(_, x):
        return x

    @graph
    def testing_io():
        end(start())

    full_job = testing_io.to_job(resource_defs={"my_loader": config_io_man})
    result = full_job.execute_in_process(
        run_config={
            "ops": {"start": {"inputs": {"x": 4}}},
        },
    )
    assert result.success
    assert result.output_for_node("end") == 4

    # test to ensure that if start is not being executed its input config is still allowed (and ignored)
    subset_result = full_job.execute_in_process(
        run_config={
            "ops": {"end": {"inputs": {"x": 1}}},
        },
        op_selection=["end"],
    )
    assert subset_result.success
    assert subset_result.output_for_node("end") == 1


def test_op_selection_on_dynamic_orchestration():
    @op
    def num_range():
        return 3

    @op(out=DynamicOut())
    def emit(num: int = 2):
        for i in range(num):
            yield DynamicOutput(value=i, mapping_key=str(i))

    @op
    def emit_ten(_):
        return 10

    @op
    def multiply_by_two(context, y):
        context.log.info("multiply_by_two is returning " + str(y * 2))
        return y * 2

    @op
    def multiply_inputs(context, y, ten):
        context.log.info("multiply_inputs is returning " + str(y * ten))
        return y * ten

    @op
    def sum_numbers(_, nums):
        return sum(nums)

    @op
    def echo(_, x: int) -> int:
        return x

    @graph
    def dynamic_graph():
        numbers = emit(num_range())
        dynamic = numbers.map(lambda num: multiply_by_two(multiply_inputs(num, emit_ten())))
        n = sum_numbers(dynamic.collect())
        echo(n)  # test transitive downstream of collect

    full_job = dynamic_graph.to_job()
    result = full_job.execute_in_process()
    assert result.success
    assert result.output_for_node("echo") == 60

    result = full_job.execute_in_process(
        op_selection=["emit*", "emit_ten"],
    )
    assert result.success
    assert result.output_for_node("echo") == 20


def test_op_selection_on_alias():
    @graph
    def _aliased():
        add_one.alias("add_one_1")(return_one.alias("return_one_1")())
        add_one.alias("add_one_2")(return_one.alias("return_one_2")())

    full_job = _aliased.to_job()
    result = full_job.execute_in_process()
    assert result.success
    assert len(_success_step_keys(result)) == 4

    subsetted_job = _aliased.to_job(op_selection=["return_one_2*"])
    result_for_subset_def = subsetted_job.execute_in_process()
    assert result_for_subset_def.success
    assert len(_success_step_keys(result_for_subset_def)) == 2

    result_for_subset = subsetted_job.execute_in_process(op_selection=["*"])
    assert result_for_subset.success
    assert len(_success_step_keys(result_for_subset)) == 2


def test_op_selection_on_implicit_alias():
    @job
    def _reuse_ops_job():
        add_one(return_one())
        add_one(return_one())
        add_one(return_one())

    result_1 = _reuse_ops_job.execute_in_process(op_selection=["return_one*"])

    assert result_1.success
    assert len(_success_step_keys(result_1)) == 2

    result_2 = _reuse_ops_job.execute_in_process(op_selection=["return_one_2*"])
    assert result_2.success
    assert len(_success_step_keys(result_2)) == 2


def test_op_selection_with_config_mapping():
    def my_config_fn(val):
        config_val = {"config": {"foo": val["foo"]}}
        return {
            "ops": {
                "my_op": config_val,
                "my_other_op": config_val,
            }
        }

    @op
    def my_op(context):
        return context.op_config["foo"]

    @graph
    def my_graph():
        my_op()
        my_op.alias("my_other_op")()

    my_job = my_graph.to_job(config=ConfigMapping(my_config_fn))
    result = my_job.execute_in_process(run_config={"foo": "bar"})
    assert result.success
    assert result.output_for_node("my_op") == "bar"
    assert result.output_for_node("my_other_op") == "bar"

    subset_result = my_job.execute_in_process(
        run_config={"foo": "bar"}, op_selection=["my_other_op"]
    )
    assert subset_result.success
    assert subset_result.output_for_node("my_other_op") == "bar"


def test_disconnected_selection():
    my_subset_job = do_it_all.to_job(op_selection=["return_two", "add_one"])
    result = my_subset_job.execute_in_process(
        run_config={"ops": {"add_one": {"inputs": {"num": 1}}}}
    )

    assert result.success

    executed_step_keys = _success_step_keys(result)
    assert len(executed_step_keys) == 2
    assert set(executed_step_keys) == {"return_two", "add_one"}


@graph
def subgraph():
    return add_one(adder(return_one(), return_two()))


@job
def supergraph():
    add_one(subgraph())


def test_nested_graph_selection_all():
    result = supergraph.execute_in_process()
    assert result.success
    assert result.output_for_node("add_one") == 5

    # select the entire subgraph
    result_graph = supergraph.execute_in_process(op_selection=["subgraph"])
    assert result_graph.success
    assert set(_success_step_keys(result_graph)) == {
        "subgraph.return_one",
        "subgraph.return_two",
        "subgraph.adder",
        "subgraph.add_one",
    }
    assert result_graph.output_for_node("subgraph") == 4


def test_nested_graph_selection_single_op():
    # select single op inside graph
    result_graph = supergraph.execute_in_process(op_selection=["subgraph.return_one"])
    assert result_graph.success
    assert set(_success_step_keys(result_graph)) == {
        "subgraph.return_one",
    }
    assert result_graph.output_for_node("subgraph.return_one") == 1


def test_nested_graph_selection_inside_graph():
    # select inside subgraph
    result_graph = supergraph.execute_in_process(
        op_selection=[
            "subgraph.return_one",
            "subgraph.return_two",
            "subgraph.adder",
        ]
    )
    assert result_graph.success
    assert set(_success_step_keys(result_graph)) == {
        "subgraph.return_one",
        "subgraph.return_two",
        "subgraph.adder",
    }
    assert result_graph.output_for_node("subgraph.adder") == 3


def test_nested_graph_selection_both_inside_and_outside_disconnected():
    # select inside subgraph (disconnected to the outside) and outside
    with pytest.raises(DagsterInvalidSubsetError):
        # can't build graph bc "subgraph" won't have output mapping but "add_one" expect output
        supergraph.execute_in_process(
            op_selection=["subgraph.adder", "add_one"],
            run_config={
                "ops": {"subgraph": {"ops": {"adder": {"inputs": {"num1": 10, "num2": 20}}}}}
            },
        )


def test_nested_graph_selection_unsatisfied_subgraph_inputs():
    # output mapping
    result_sub_1 = supergraph.execute_in_process(
        op_selection=["subgraph.return_one", "subgraph.adder", "subgraph.add_one", "add_one"],
        run_config={"ops": {"subgraph": {"ops": {"adder": {"inputs": {"num2": 0}}}}}},
    )
    assert result_sub_1.success
    assert set(_success_step_keys(result_sub_1)) == {
        "subgraph.return_one",
        "subgraph.adder",
        "subgraph.add_one",
        "add_one",
    }
    assert result_sub_1.output_for_node("add_one") == 3

    # no output mapping
    result_sub_2 = supergraph.execute_in_process(
        op_selection=["subgraph.return_one", "subgraph.adder", "subgraph.add_one"],
        run_config={"ops": {"subgraph": {"ops": {"adder": {"inputs": {"num2": 100}}}}}},
    )
    assert result_sub_2.success
    assert set(_success_step_keys(result_sub_2)) == {
        "subgraph.return_one",
        "subgraph.adder",
        "subgraph.add_one",
    }
    assert result_sub_2.output_for_node("subgraph.add_one") == 102


def test_nested_graph_selection_input_mapping():
    @graph
    def _subgraph(x):
        return add_one(adder.alias("aliased_adder")(return_one(), x))

    @job
    def _super():
        add_one(_subgraph(return_two()))

    # graph subset has input mapping
    result_sub_1 = _super.execute_in_process(
        op_selection=["return_two", "_subgraph.return_one", "_subgraph.aliased_adder"],
    )
    assert result_sub_1.success
    assert set(_success_step_keys(result_sub_1)) == {
        "return_two",
        "_subgraph.return_one",
        "_subgraph.aliased_adder",
    }
    assert result_sub_1.output_for_node("_subgraph.aliased_adder") == 3

    # graph subset doesn't have input mapping
    result_sub_2 = _super.execute_in_process(
        op_selection=["_subgraph.return_one", "_subgraph.aliased_adder"],
        run_config={"ops": {"_subgraph": {"inputs": {"x": {"value": 100}}}}},
    )
    assert result_sub_2.success
    assert set(_success_step_keys(result_sub_2)) == {
        "_subgraph.return_one",
        "_subgraph.aliased_adder",
    }
    assert result_sub_2.output_for_node("_subgraph.aliased_adder") == 101


def test_sub_sub_graph_selection():
    @graph
    def subsubgraph():
        return add_one(return_one())

    @graph
    def _subgraph():
        return add_one(subsubgraph())

    @job
    def _super():
        add_one(_subgraph())

    result_full = _super.execute_in_process()
    assert set(_success_step_keys(result_full)) == {
        "_subgraph.subsubgraph.return_one",
        "_subgraph.subsubgraph.add_one",
        "_subgraph.add_one",
        "add_one",
    }
    assert result_full.output_for_node("add_one") == 4

    # select sub sub
    result_sub_1 = _super.execute_in_process(op_selection=["_subgraph.subsubgraph.return_one"])
    assert set(_success_step_keys(result_sub_1)) == {
        "_subgraph.subsubgraph.return_one",
    }
    assert result_sub_1.output_for_node("_subgraph.subsubgraph.return_one") == 1

    # select sub all
    result_sub_2 = _super.execute_in_process(op_selection=["_subgraph"])
    assert set(_success_step_keys(result_sub_2)) == {
        "_subgraph.subsubgraph.return_one",
        "_subgraph.subsubgraph.add_one",
        "_subgraph.add_one",
    }
    assert result_sub_2.output_for_node("_subgraph") == 3

    # select sub with unsatisfied input
    result_sub_3 = _super.execute_in_process(
        op_selection=["_subgraph.add_one"],
        run_config={"ops": {"_subgraph": {"ops": {"add_one": {"inputs": {"num": 100}}}}}},
    )
    assert set(_success_step_keys(result_sub_3)) == {
        "_subgraph.add_one",
    }
    assert result_sub_3.output_for_node("_subgraph.add_one") == 101

    # select sub sub with unsatisfied input
    result_sub_4 = _super.execute_in_process(
        op_selection=["_subgraph.subsubgraph.add_one"],
        run_config={
            "ops": {
                "_subgraph": {
                    "ops": {"subsubgraph": {"ops": {"add_one": {"inputs": {"num": 200}}}}}
                }
            }
        },
    )
    assert set(_success_step_keys(result_sub_4)) == {
        "_subgraph.subsubgraph.add_one",
    }
    assert result_sub_4.output_for_node("_subgraph.subsubgraph.add_one") == 201


def test_nested_op_selection_fan_in():
    @op
    def sum_fan_in(nums: List[int]) -> int:
        return sum(nums)

    @graph
    def fan_in_graph():
        fan_outs = []
        for i in range(0, 10):
            fan_outs.append(return_one.alias(f"return_one_{i}")())
        return sum_fan_in(fan_outs)

    @job
    def _super():
        add_one(fan_in_graph())

    result_full = _super.execute_in_process()
    assert result_full.success
    assert result_full.output_for_node("add_one") == 11

    result_sub_1 = _super.execute_in_process(
        op_selection=[
            "fan_in_graph.return_one_0",
            "fan_in_graph.return_one_1",
            "fan_in_graph.return_one_2",
            "fan_in_graph.sum_fan_in",
            "add_one",
        ]
    )
    assert result_sub_1.success
    assert result_sub_1.output_for_node("add_one") == 4


def test_nested_op_selection_with_config_mapping():
    @op(config_schema=str)
    def concat(context, x: str):
        return x + context.op_config

    @op(config_schema=str)
    def my_op(context):
        return context.op_config

    def _nested_config_fn(outer):
        return {"my_op": {"config": outer}, "concat": {"config": outer}}

    @graph(config=ConfigMapping(config_fn=_nested_config_fn, config_schema=str))
    def my_nested_graph():
        concat(my_op())

    def _config_fn(outer):
        return {"my_nested_graph": {"config": outer}}

    @graph(config=ConfigMapping(config_fn=_config_fn, config_schema=str))
    def my_graph():
        my_nested_graph()

    result = my_graph.to_job().execute_in_process(run_config={"ops": {"config": "foo"}})
    assert result.success
    assert result.output_for_node("my_nested_graph.concat") == "foofoo"

    result_sub_1 = my_graph.to_job().execute_in_process(
        op_selection=["my_nested_graph.my_op", "my_nested_graph.concat"],
        run_config={"ops": {"config": "hello"}},
    )
    assert result_sub_1.success
    assert result_sub_1.output_for_node("my_nested_graph.concat") == "hellohello"

    # when config mapping generates values for unselected nodes, the excess values are ignored
    result_sub_2 = my_graph.to_job().execute_in_process(
        op_selection=["my_nested_graph.my_op"],
        run_config={"ops": {"config": "hello"}},
    )
    assert result_sub_2.success
    assert result_sub_2.output_for_node("my_nested_graph.my_op") == "hello"

    # sub sub graph
    @graph
    def my_super_graph():
        my_graph()

    my_subselected_super_job = my_super_graph.to_job(
        op_selection=["my_graph.my_nested_graph.my_op"]
    )
    result_sub_3_1 = my_subselected_super_job.execute_in_process(
        run_config={"ops": {"my_graph": {"config": "hello"}}},
    )
    assert result_sub_3_1.success
    assert set(_success_step_keys(result_sub_3_1)) == {"my_graph.my_nested_graph.my_op"}
    assert result_sub_3_1.output_for_node("my_graph.my_nested_graph.my_op") == "hello"

    # execute a subselected job with op_selection
    result_sub_3_2 = my_subselected_super_job.execute_in_process(
        op_selection=["*"],
        run_config={"ops": {"my_graph": {"config": "hello"}}},
    )
    assert result_sub_3_2.success
    assert set(_success_step_keys(result_sub_3_2)) == {"my_graph.my_nested_graph.my_op"}
    assert result_sub_3_2.output_for_node("my_graph.my_nested_graph.my_op") == "hello"
