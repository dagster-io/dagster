from dagster import (
    Any,
    Bool,
    Dict,
    Float,
    InputDefinition,
    Int,
    List,
    Optional,
    OutputDefinition,
    Set,
    String,
    Tuple,
    execute_solid,
    solid,
)


@solid(
    input_defs=[InputDefinition("x", dagster_type=Any)],
    output_defs=[OutputDefinition(dagster_type=Any)],
)
def identity_py2(_, x):
    return x


@solid(
    input_defs=[InputDefinition("x", dagster_type=Bool)],
    output_defs=[OutputDefinition(dagster_type=String)],
)
def boolean_py2(_, x):
    return "true" if x else "false"


@solid(
    input_defs=[InputDefinition("x", dagster_type=String)],
    output_defs=[OutputDefinition(dagster_type=bool)],
)
def empty_string_py2(_, x):
    return len(x) == 0


@solid(
    input_defs=[InputDefinition("x", dagster_type=Int)],
    output_defs=[OutputDefinition(dagster_type=int)],
)
def add_3_py2(_, x):
    return x + 3


@solid(
    input_defs=[InputDefinition("x", dagster_type=Float)],
    output_defs=[OutputDefinition(dagster_type=float)],
)
def div_2_py_2(_, x):
    return x / 2


@solid(
    input_defs=[InputDefinition("x", dagster_type=String), InputDefinition("y", dagster_type=str)],
    output_defs=[OutputDefinition(dagster_type=str)],
)
def concat_py_2(_, x, y):
    return x + y


@solid(
    input_defs=[
        InputDefinition("x", dagster_type=String),
        InputDefinition("y", dagster_type=Optional[String]),
    ],
    output_defs=[OutputDefinition(dagster_type=String)],
)
def nullable_concat_py2(_, x, y):
    return x + (y or "")


@solid(
    input_defs=[InputDefinition("xs", dagster_type=List[String])],
    output_defs=[OutputDefinition(dagster_type=String)],
)
def concat_list_py2(_, xs):
    return "".join(xs)


@solid(
    input_defs=[InputDefinition("spec", dagster_type=Dict)], output_defs=[OutputDefinition(String)]
)
def repeat_py2(_, spec):
    return spec["word"] * spec["times"]


@solid(
    input_defs=[InputDefinition("set_input", dagster_type=Set[String])],
    output_defs=[OutputDefinition(List[String])],
)
def set_solid_py2(_, set_input):
    return sorted([x for x in set_input])


@solid(
    input_defs=[InputDefinition("tuple_input", dagster_type=Tuple[String, Int, Float])],
    output_defs=[OutputDefinition(List)],
)
def tuple_solid_py2(_, tuple_input):
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
    res = execute_solid(set_solid_py2, input_values={"set_input": {"foo", "bar", "baz"}})
    assert res.output_value() == sorted(["foo", "bar", "baz"])


def test_tuple_solid_py2():
    res = execute_solid(tuple_solid_py2, input_values={"tuple_input": ("foo", 1, 3.1)})
    assert res.output_value() == ["foo", 1, 3.1]
