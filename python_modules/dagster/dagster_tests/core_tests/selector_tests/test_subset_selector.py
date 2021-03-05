import pytest
from dagster import InputDefinition, lambda_solid, pipeline
from dagster.core.errors import DagsterExecutionStepNotFoundError, DagsterInvalidSubsetError
from dagster.core.selector.subset_selector import (
    MAX_NUM,
    Traverser,
    generate_dep_graph,
    parse_clause,
    parse_solid_selection,
    parse_step_selection,
)


@lambda_solid
def return_one():
    return 1


@lambda_solid
def return_two():
    return 2


@lambda_solid(input_defs=[InputDefinition("num1"), InputDefinition("num2")])
def add_nums(num1, num2):
    return num1 + num2


@lambda_solid(input_defs=[InputDefinition("num")])
def multiply_two(num):
    return num * 2


@lambda_solid(input_defs=[InputDefinition("num")])
def add_one(num):
    return num + 1


@pipeline
def foo_pipeline():
    """
    return_one ---> add_nums --> multiply_two --> add_one
    return_two --|
    """
    add_one(multiply_two(add_nums(return_one(), return_two())))


def test_generate_dep_graph():
    graph = generate_dep_graph(foo_pipeline)
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
    graph = generate_dep_graph(foo_pipeline)
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
    graph = generate_dep_graph(foo_pipeline)
    traverser = Traverser(graph)

    assert traverser.fetch_upstream(item_name="some_solid", depth=1) == set()


def test_parse_clause():
    assert parse_clause("some_solid") == (0, "some_solid", 0)
    assert parse_clause("*some_solid") == (MAX_NUM, "some_solid", 0)
    assert parse_clause("some_solid+") == (0, "some_solid", 1)
    assert parse_clause("+some_solid+") == (1, "some_solid", 1)
    assert parse_clause("*some_solid++") == (MAX_NUM, "some_solid", 2)


def test_parse_clause_invalid():
    assert parse_clause("1+some_solid") == None


def test_parse_solid_selection_single():
    solid_selection_single = parse_solid_selection(foo_pipeline, ["add_nums"])
    assert len(solid_selection_single) == 1
    assert solid_selection_single == {"add_nums"}

    solid_selection_star = parse_solid_selection(foo_pipeline, ["add_nums*"])
    assert len(solid_selection_star) == 3
    assert set(solid_selection_star) == {"add_nums", "multiply_two", "add_one"}

    solid_selection_both = parse_solid_selection(foo_pipeline, ["*add_nums+"])
    assert len(solid_selection_both) == 4
    assert set(solid_selection_both) == {"return_one", "return_two", "add_nums", "multiply_two"}


def test_parse_solid_selection_multi():
    solid_selection_multi_disjoint = parse_solid_selection(
        foo_pipeline, ["return_one", "add_nums+"]
    )
    assert len(solid_selection_multi_disjoint) == 3
    assert set(solid_selection_multi_disjoint) == {"return_one", "add_nums", "multiply_two"}

    solid_selection_multi_overlap = parse_solid_selection(
        foo_pipeline, ["*add_nums", "return_one+"]
    )
    assert len(solid_selection_multi_overlap) == 3
    assert set(solid_selection_multi_overlap) == {"return_one", "return_two", "add_nums"}

    with pytest.raises(
        DagsterInvalidSubsetError,
        match="No qualified solids to execute found for solid_selection",
    ):
        parse_solid_selection(foo_pipeline, ["*add_nums", "a"])


def test_parse_solid_selection_invalid():

    with pytest.raises(
        DagsterInvalidSubsetError,
        match="No qualified solids to execute found for solid_selection",
    ):
        parse_solid_selection(foo_pipeline, ["some,solid"])


step_deps = {
    "return_one": set(),
    "return_two": set(),
    "add_nums": {"return_one", "return_two"},
    "multiply_two": {"add_nums"},
    "add_one": {"multiply_two"},
}


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
        DagsterExecutionStepNotFoundError,
        match="Step selection refers to unknown step: a",
    ):
        parse_step_selection(step_deps, ["*add_nums", "a"])


def test_parse_step_selection_invalid():

    with pytest.raises(
        DagsterInvalidSubsetError,
        match="No qualified steps to execute found for step_selection",
    ):
        parse_step_selection(step_deps, ["1+some_solid"])
