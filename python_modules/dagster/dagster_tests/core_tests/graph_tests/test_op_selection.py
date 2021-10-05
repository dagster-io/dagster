from dagster import graph, op
from dagster.core.events import DagsterEventType


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


def test_simple_op_selection_on_job_def():
    my_subset_job = do_it_all.to_job(op_selection=["*adder"])
    result = my_subset_job.execute_in_process()

    assert result.success

    executed_step_keys = [
        evt.step_key for evt in result.event_list if evt.event_type == DagsterEventType.STEP_SUCCESS
    ]
    assert len(executed_step_keys) == 3
    assert "add_one" not in [executed_step_keys]


@graph
def larger_graph():
    do_it_all()
    return_one()


def test_nested_op_selection_on_job_def():
    my_subset_job = larger_graph.to_job(op_selection=["*do_it_all.adder", "return_one"])
    result = my_subset_job.execute_in_process()

    assert result.success
    executed_step_keys = [
        evt.step_key for evt in result.event_list if evt.event_type == DagsterEventType.STEP_SUCCESS
    ]
    assert len(executed_step_keys) == 4
    assert "add_one" not in [executed_step_keys]
