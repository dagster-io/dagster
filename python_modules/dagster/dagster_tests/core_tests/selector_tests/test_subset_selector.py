import dagster as dg
import pytest
from dagster import in_process_executor
from dagster._core.selector.subset_selector import (
    MAX_NUM,
    Traverser,
    clause_to_subset,
    generate_dep_graph,
    parse_clause,
    parse_op_queries,
    parse_step_selection,
)


@dg.op
def return_one():
    return 1


@dg.op
def return_two():
    return 2


@dg.op(ins={"num1": dg.In(), "num2": dg.In()})
def add_nums(num1, num2):
    return num1 + num2


@dg.op(ins={"num": dg.In()})
def multiply_two(num):
    return num * 2


@dg.op(ins={"num": dg.In()})
def add_one(num):
    return num + 1


@dg.job(executor_def=in_process_executor)
def foo_job():
    """return_one ---> add_nums --> multiply_two --> add_one
    return_two --|.
    """
    add_one(multiply_two(add_nums(return_one(), return_two())))


def test_generate_dep_graph():
    graph = generate_dep_graph(foo_job)  # pyright: ignore[reportArgumentType]
    assert graph == {
        "upstream": {
            "return_one": set(),
            "return_two": set(),
            "add_nums": {"return_one", "return_two"},
            "multiply_two": {"add_nums"},
            "add_one": {"multiply_two"},
        },
        "downstream": {
            "return_one": {"add_nums"},
            "return_two": {"add_nums"},
            "add_nums": {"multiply_two"},
            "multiply_two": {"add_one"},
            "add_one": set(),
        },
    }


def test_traverser():
    graph = generate_dep_graph(foo_job)  # pyright: ignore[reportArgumentType]
    traverser = Traverser(graph)

    assert traverser.fetch_upstream(item_name="return_one", depth=1) == set()
    assert traverser.fetch_downstream(item_name="return_one", depth=1) == {"add_nums"}
    assert traverser.fetch_upstream(item_name="multiply_two", depth=0) == set()
    assert traverser.fetch_upstream(item_name="multiply_two", depth=2) == {
        "add_nums",
        "return_one",
        "return_two",
    }
    assert traverser.fetch_downstream(item_name="multiply_two", depth=2) == {"add_one"}


def test_traverser_invalid():
    graph = generate_dep_graph(foo_job)  # pyright: ignore[reportArgumentType]
    traverser = Traverser(graph)

    assert traverser.fetch_upstream(item_name="some_solid", depth=1) == set()


def test_parse_clause():
    assert parse_clause("some_solid") == (0, "some_solid", 0)
    assert parse_clause("*some_solid") == (MAX_NUM, "some_solid", 0)
    assert parse_clause("some_solid+") == (0, "some_solid", 1)
    assert parse_clause("+some_solid+") == (1, "some_solid", 1)
    assert parse_clause("*some_solid++") == (MAX_NUM, "some_solid", 2)


def test_parse_clause_invalid():
    assert parse_clause("1+some_solid") is None


def test_parse_op_selection_single():
    op_selection_single = parse_op_queries(foo_job, ["add_nums"])  # pyright: ignore[reportArgumentType]
    assert len(op_selection_single) == 1
    assert op_selection_single == {"add_nums"}

    op_selection_star = parse_op_queries(foo_job, ["add_nums*"])  # pyright: ignore[reportArgumentType]
    assert len(op_selection_star) == 3
    assert set(op_selection_star) == {"add_nums", "multiply_two", "add_one"}

    op_selection_both = parse_op_queries(foo_job, ["*add_nums+"])  # pyright: ignore[reportArgumentType]
    assert len(op_selection_both) == 4
    assert set(op_selection_both) == {
        "return_one",
        "return_two",
        "add_nums",
        "multiply_two",
    }


def test_parse_op_selection_multi():
    op_selection_multi_disjoint = parse_op_queries(foo_job, ["return_one", "add_nums+"])  # pyright: ignore[reportArgumentType]
    assert len(op_selection_multi_disjoint) == 3
    assert set(op_selection_multi_disjoint) == {
        "return_one",
        "add_nums",
        "multiply_two",
    }

    op_selection_multi_overlap = parse_op_queries(foo_job, ["*add_nums", "return_one+"])  # pyright: ignore[reportArgumentType]
    assert len(op_selection_multi_overlap) == 3
    assert set(op_selection_multi_overlap) == {
        "return_one",
        "return_two",
        "add_nums",
    }

    with pytest.raises(
        dg.DagsterInvalidSubsetError,
        match="No qualified ops to execute found for op_selection",
    ):
        parse_op_queries(foo_job, ["*add_nums", "a"])  # pyright: ignore[reportArgumentType]


def test_parse_op_selection_invalid():
    with pytest.raises(
        dg.DagsterInvalidSubsetError,
        match="No qualified ops to execute found for op_selection",
    ):
        parse_op_queries(foo_job, ["some,solid"])  # pyright: ignore[reportArgumentType]


step_deps = {
    "return_one": set(),
    "return_two": set(),
    "add_nums": {"return_one", "return_two"},
    "multiply_two": {"add_nums"},
    "add_one": {"multiply_two"},
}


@pytest.mark.parametrize(
    "clause,expected_subset",
    [
        ("a", "a"),
        ("b+", "b,c,d"),
        ("+f", "f,d,e"),
        ("++f", "f,d,e,c,a,b"),
        ("+++final", "final,a,d,start,b"),
        ("b++", "b,c,d,e,f,final"),
        ("start*", "start,a,d,f,final"),
    ],
)
def test_clause_to_subset(clause, expected_subset):
    graph = {
        "upstream": {
            "start": set(),
            "a": {"start"},
            "b": set(),
            "c": {"b"},
            "d": {"a", "b"},
            "e": {"c"},
            "f": {"e", "d"},
            "final": {"a", "d"},
        },
        "downstream": {
            "start": {"a"},
            "b": {"c", "d"},
            "a": {"final", "d"},
            "c": {"e"},
            "d": {"final", "f"},
            "e": {"f"},
        },
    }
    assert set(clause_to_subset(graph, clause, lambda x: x)) == set(expected_subset.split(","))  # pyright: ignore[reportArgumentType]


def test_parse_step_selection_single():
    step_selection_single = parse_step_selection(step_deps, ["add_nums"])
    assert len(step_selection_single) == 1
    assert step_selection_single == {"add_nums"}

    step_selection_star = parse_step_selection(step_deps, ["add_nums*"])
    assert len(step_selection_star) == 3
    assert set(step_selection_star) == {
        "add_nums",
        "multiply_two",
        "add_one",
    }

    step_selection_both = parse_step_selection(step_deps, ["*add_nums+"])
    assert len(step_selection_both) == 4
    assert set(step_selection_both) == {
        "return_one",
        "return_two",
        "add_nums",
        "multiply_two",
    }


def test_parse_step_selection_multi():
    step_selection_multi_disjoint = parse_step_selection(step_deps, ["return_one", "add_nums+"])
    assert len(step_selection_multi_disjoint) == 3
    assert set(step_selection_multi_disjoint) == {
        "return_one",
        "add_nums",
        "multiply_two",
    }

    step_selection_multi_overlap = parse_step_selection(step_deps, ["*add_nums", "return_one+"])
    assert len(step_selection_multi_overlap) == 3
    assert set(step_selection_multi_overlap) == {
        "return_one",
        "return_two",
        "add_nums",
    }

    with pytest.raises(
        dg.DagsterExecutionStepNotFoundError,
        match="Step selection refers to unknown step: a",
    ):
        parse_step_selection(step_deps, ["*add_nums", "a"])


def test_parse_step_selection_invalid():
    with pytest.raises(
        dg.DagsterInvalidSubsetError,
        match="No qualified steps to execute found for step_selection",
    ):
        parse_step_selection(step_deps, ["1+some_solid"])


@dg.asset
def my_asset(context):
    assert context.job_def.asset_selection_data is not None
    return 1


@dg.asset
def asset_2(my_asset):
    return my_asset


@dg.repository
def asset_house():
    return [
        my_asset,
        asset_2,
        dg.define_asset_job("asset_selection_job", selection="*", executor_def=in_process_executor),
    ]


def get_asset_selection_job():
    return asset_house.get_job("asset_selection_job")
