from dagster import (
    In,
    Out,
    op,
    Any,
    Bool,
    Dict,
    Float,
    Int,
    List,
    Optional,
    Set,
    String,
    Tuple,
)
from dagster._legacy import InputDefinition, OutputDefinition, execute_solid, solid


@op(
    ins={"x": In(dagster_type=Any)},
    out=Out(dagster_type=Any),
)
def identity_py2(_, x):
    return x


@op(
    ins={"x": In(dagster_type=Bool)},
    out=Out(dagster_type=String),
)
def boolean_py2(_, x):
    return "true" if x else "false"


@op(
    ins={"x": In(dagster_type=String)},
    out=Out(dagster_type=bool),
)
def empty_string_py2(_, x):
    return len(x) == 0


@op(
    ins={"x": In(dagster_type=Int)},
    out=Out(dagster_type=int),
)
def add_3_py2(_, x):
    return x + 3


@op(
    ins={"x": In(dagster_type=Float)},
    out=Out(dagster_type=float),
)
def div_2_py_2(_, x):
    return x / 2


@op(
    ins={"x": In(dagster_type=String), "y": In(dagster_type=str)},
    out=Out(dagster_type=str),
)
def concat_py_2(_, x, y):
    return x + y


@op(
    ins={"x": In(dagster_type=String), "y": In(dagster_type=Optional[String])},
    out=Out(dagster_type=String),
)
def nullable_concat_py2(_, x, y):
    return x + (y or "")


@op(
    ins={"xs": In(dagster_type=List[String])},
    out=Out(dagster_type=String),
)
def concat_list_py2(_, xs):
    return "".join(xs)


@op(
    ins={"spec": In(dagster_type=Dict)},
    out=Out(String),
)
def repeat_py2(_, spec):
    return spec["word"] * spec["times"]


@op(
    ins={"set_input": In(dagster_type=Set[String])},
    out=Out(List[String]),
)
def set_op_py2(_, set_input):
    return sorted([x for x in set_input])


@op(
    ins={"tuple_input": In(dagster_type=Tuple[String, Int, Float])},
    out=Out(List),
)
def tuple_op_py2(_, tuple_input):
    return [x for x in tuple_input]


def test_identity_py2():
    res = execute_solid(identity_py2, input_values={"x": "foo"})
    assert res.output_value() == "foo"


def test_boolean_py2():
    res = execute_solid(boolean_py2, input_values={"x": True})
    assert res.output_value() == "true"

    res = execute_solid(boolean_py2, input_values={"x": False})
    assert res.output_value() == "false"


def test_empty_string_py2():
    res = execute_solid(empty_string_py2, input_values={"x": ""})
    assert res.output_value() is True

    res = execute_solid(empty_string_py2, input_values={"x": "foo"})
    assert res.output_value() is False


def test_add_3_py2():
    res = execute_solid(add_3_py2, input_values={"x": 3})
    assert res.output_value() == 6


def test_div_2_py2():
    res = execute_solid(div_2_py_2, input_values={"x": 7.0})
    assert res.output_value() == 3.5


def test_concat_py2():
    res = execute_solid(concat_py_2, input_values={"x": "foo", "y": "bar"})
    assert res.output_value() == "foobar"


def test_nullable_concat_py2():
    res = execute_solid(nullable_concat_py2, input_values={"x": "foo", "y": None})
    assert res.output_value() == "foo"


def test_concat_list_py2():
    res = execute_solid(concat_list_py2, input_values={"xs": ["foo", "bar", "baz"]})
    assert res.output_value() == "foobarbaz"


def test_repeat_py2():
    res = execute_solid(repeat_py2, input_values={"spec": {"word": "foo", "times": 3}})
    assert res.output_value() == "foofoofoo"


def test_set_solid_py2():
    res = execute_solid(set_op_py2, input_values={"set_input": {"foo", "bar", "baz"}})
    assert res.output_value() == sorted(["foo", "bar", "baz"])


def test_tuple_solid_py2():
    res = execute_solid(tuple_op_py2, input_values={"tuple_input": ("foo", 1, 3.1)})
    assert res.output_value() == ["foo", 1, 3.1]
