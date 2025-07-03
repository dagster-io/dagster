import collections

import dagster as dg
from dagster._core.types.dagster_type import resolve_dagster_type


def test_dagster_type_decorator():
    @dg.usable_as_dagster_type(name=None)
    class Foo:
        pass

    @dg.usable_as_dagster_type()
    class Bar:
        pass

    @dg.usable_as_dagster_type
    class Baaz:
        pass

    assert resolve_dagster_type(Foo).unique_name == "Foo"
    assert resolve_dagster_type(Bar).unique_name == "Bar"
    assert resolve_dagster_type(Baaz).unique_name == "Baaz"


def test_dagster_type_decorator_name_desc():
    @dg.usable_as_dagster_type(name="DifferentName", description="desc")
    class Something:
        pass

    dagster_type = resolve_dagster_type(Something)
    assert dagster_type.unique_name == "DifferentName"
    assert dagster_type.description == "desc"


def test_make_dagster_type():
    SomeNamedTuple = collections.namedtuple("SomeNamedTuple", "prop")
    DagsterSomeNamedTuple = dg.PythonObjectDagsterType(SomeNamedTuple)
    dagster_type = resolve_dagster_type(DagsterSomeNamedTuple)
    assert dagster_type.unique_name == "SomeNamedTuple"
    assert SomeNamedTuple(prop="foo").prop == "foo"

    DagsterNewNameNamedTuple = dg.PythonObjectDagsterType(SomeNamedTuple, name="OverwriteName")
    dagster_type = resolve_dagster_type(DagsterNewNameNamedTuple)
    assert dagster_type.unique_name == "OverwriteName"
