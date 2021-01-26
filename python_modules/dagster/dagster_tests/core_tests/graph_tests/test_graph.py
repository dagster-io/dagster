from dagster import solid
from dagster.core.definitions.decorators.graph import graph
from dagster.core.definitions.graph import GraphDefinition


def test_basic_graph():
    @solid
    def emit_one(_):
        return 1

    @solid
    def add(_, x, y):
        return x + y

    @graph
    def add_one(a):
        return add(emit_one(), a)

    assert isinstance(add_one, GraphDefinition)
