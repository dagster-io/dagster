from dagster import solid
from dagster.core.definitions.decorators.graph import graph
from dagster.core.definitions.graph import GraphDefinition
from dagster.core.execution.execute import execute_in_process


def get_solids():
    @solid
    def emit_one(_):
        return 1

    @solid
    def add(_, x, y):
        return x + y

    return emit_one, add


def test_basic_graph():
    emit_one, add = get_solids()

    @graph
    def get_two():
        return add(emit_one(), emit_one())

    assert isinstance(get_two, GraphDefinition)

    result = execute_in_process(get_two)

    assert result.success


def test_composite_graph():
    emit_one, add = get_solids()

    @graph
    def add_one(x):
        return add(emit_one(), x)

    @graph
    def add_two(x):
        return add(add_one(x), emit_one())

    assert isinstance(add_two, GraphDefinition)
