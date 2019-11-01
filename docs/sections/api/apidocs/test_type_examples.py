import os
import pickle
import tempfile
import time

from dagster import (
    Any,
    Bool,
    Dict,
    Field,
    Float,
    InputDefinition,
    Int,
    List,
    Nothing,
    Optional,
    OutputDefinition,
    Path,
    String,
    execute_pipeline,
    execute_solid,
    pipeline,
    solid,
)


@solid
def identity(_, x: Any) -> Any:
    return x


@solid
def identity_imp(_, x):
    return x


@solid(
    input_defs=[InputDefinition('x', dagster_type=Any)],
    output_defs=[OutputDefinition(dagster_type=Any)]
)
def identity_py2(_, x):
    return x


@solid
def boolean(_, x: Bool) -> String:
    return 'true' if x else 'false'


@solid
def empty_string(_, x: String) -> bool:
    return len(x) == 0


@solid(
    input_defs=[InputDefinition('x', dagster_type=Bool)],
    output_defs=[OutputDefinition(dagster_type=String)]
)
def boolean_py2(_, x):
    return 'true' if x else 'false'


@solid(
    input_defs=[InputDefinition('x', dagster_type=String)],
    output_defs=[OutputDefinition(dagster_type=bool)]
)
def empty_string_py2(_, x):
    return len(x) == 0


@solid
def add_3(_, x: Int) -> int:
    return x + 3


@solid(
    input_defs=[InputDefinition('x', dagster_type=Int)],
    output_defs=[OutputDefinition(dagster_type=int)]
)
def add_3_py2(_, x):
    return x + 3


@solid
def div_2(_, x: Float) -> float:
    return x / 2


@solid(
    input_defs=[InputDefinition('x', dagster_type=Float)],
    output_defs=[OutputDefinition(dagster_type=float)]
)
def div_2_py_2(_, x):
    return x / 2


@solid
def concat(_, x: String, y: str) -> str:
    return x + y


@solid(
    input_defs=[InputDefinition('x', dagster_type=String), InputDefinition('y', dagster_type=str)],
    output_defs=[OutputDefinition(dagster_type=str)]
)
def concat_py_2(_, x, y):
    return x + y


@solid
def exists(_, path: Path) -> Bool:
    return os.path.exists(path)


@solid(
    input_defs=[InputDefinition('path', dagster_type=Path)],
    output_defs=[OutputDefinition(dagster_type=Bool)]
)
def exists_py2(_, path):
    return os.path.exists(path)


@solid
def wait(_) -> Nothing:
    time.sleep(1)
    return


@solid(
    input_defs=[InputDefinition('ready', dagster_type=Nothing)]
)
def done(_) -> str:
    return 'done'


@pipeline
def nothing_pipeline():
    done(wait())


@solid
def wait_int(_) -> Int:
    time.sleep(1)
    return 1


@pipeline
def nothing_int_pipeline():
    done(wait_int())


@solid
def nullable_concat(_, x: String, y: Optional[String]) -> String:
    return x + (y or '')


@solid(
    input_defs=[
        InputDefinition('x', dagster_type=String),
        InputDefinition('y', dagster_type=Optional[String])
    ],
    output_defs=[OutputDefinition(dagster_type=String)]
)
def nullable_concat_py2(_, x, y) -> String:
    return x + (y or '')


@solid
def concat_list(_, xs: List[String]) -> String:
    return ''.join(xs)


@solid(
    input_defs=[InputDefinition('xs', dagster_type=List[String])],
    output_defs=[OutputDefinition(dagster_type=String)]
)
def concat_list_py2(_, xs) -> String:
    return ''.join(xs)


@solid
def emit_1(_) -> int:
    return 1


@solid
def emit_2(_) -> int:
    return 2


@solid
def emit_3(_) -> int:
    return 3


@solid
def sum_solid(_, xs: List[int]) -> int:
    return sum(xs)


@pipeline
def sum_pipeline():
    sum_solid([emit_1(), emit_2(), emit_3()])


@solid
def repeat(_, spec: Dict) -> str:
    return spec['word'] * spec['times']


@solid(
    input_defs=[InputDefinition('spec', dagster_type=Dict)],
    output_defs=[OutputDefinition(String)]
)
def repeat_py2(_, spec):
    return spec['word'] * spec['times']


def test_identity():
    res = execute_solid(identity, input_values={'x': 'foo'})
    assert res.output_value() == 'foo'


def test_identity_imp():
    res = execute_solid(identity_imp, input_values={'x': 'foo'})
    assert res.output_value() == 'foo'


def test_identity_py2():
    res = execute_solid(identity_py2, input_values={'x': 'foo'})
    assert res.output_value() == 'foo'


def test_boolean():
    res = execute_solid(boolean, input_values={'x': True})
    assert res.output_value() == 'true'

    res = execute_solid(boolean, input_values={'x': False})
    assert res.output_value() == 'false'


def test_empty_string():
    res = execute_solid(empty_string, input_values={'x': ''})
    assert res.output_value() is True

    res = execute_solid(empty_string, input_values={'x': 'foo'})
    assert res.output_value() is False


def test_boolean_py2():
    res = execute_solid(boolean_py2, input_values={'x': True})
    assert res.output_value() == 'true'

    res = execute_solid(boolean_py2, input_values={'x': False})
    assert res.output_value() == 'false'


def test_empty_string_py2():
    res = execute_solid(empty_string_py2, input_values={'x': ''})
    assert res.output_value() is True

    res = execute_solid(empty_string_py2, input_values={'x': 'foo'})
    assert res.output_value() is False


def test_add_3():
    res = execute_solid(add_3, input_values={'x': 3})
    assert res.output_value() == 6


def test_add_3_py2():
    res = execute_solid(add_3_py2, input_values={'x': 3})
    assert res.output_value() == 6


def test_div_2():
    res = execute_solid(div_2, input_values={'x': 7.})
    assert res.output_value() == 3.5


def test_div_2_py2():
    res = execute_solid(div_2_py_2, input_values={'x': 7.})
    assert res.output_value() == 3.5


def test_concat():
    res = execute_solid(concat, input_values={'x': 'foo', 'y': 'bar'})
    assert res.output_value() == 'foobar'


def test_concat_py2():
    res = execute_solid(concat_py_2, input_values={'x': 'foo', 'y': 'bar'})
    assert res.output_value() == 'foobar'


def test_exists():
    res = execute_solid(exists, input_values={'path': 'garkjgh.dkjhfk'})
    assert res.output_value() is False


def test_exists_py2():
    res = execute_solid(exists_py2, input_values={'path': 'garkjgh.dkjhfk'})
    assert res.output_value() is False


def test_nothing_pipeline():
    res = execute_pipeline(nothing_pipeline)
    assert res.result_for_solid('wait').output_value() is None
    assert res.result_for_solid('done').output_value() == 'done'


def test_nothing_int_pipeline():
    res = execute_pipeline(nothing_int_pipeline)
    assert res.result_for_solid('wait_int').output_value() == 1
    assert res.result_for_solid('done').output_value() == 'done'


def test_nullable_concat():
    res = execute_solid(nullable_concat, input_values={'x': 'foo', 'y': None})
    assert res.output_value() == 'foo'


def test_nullable_concat_py2():
    res = execute_solid(nullable_concat_py2, input_values={'x': 'foo', 'y': None})
    assert res.output_value() == 'foo'


def test_concat_list():
    res = execute_solid(concat_list, input_values={'xs': ['foo', 'bar', 'baz']})
    assert res.output_value() == 'foobarbaz'


def test_concat_list_py2():
    res = execute_solid(concat_list_py2, input_values={'xs': ['foo', 'bar', 'baz']})
    assert res.output_value() == 'foobarbaz'


def test_sum_pipeline():
    res = execute_pipeline(sum_pipeline)
    assert res.result_for_solid('sum_solid').output_value() == 6


def test_repeat():
    res = execute_solid(repeat, input_values={'spec': {'word': 'foo', 'times': 3}})
    assert res.output_value() == 'foofoofoo'


def test_repeat_py2():
    res = execute_solid(repeat_py2, input_values={'spec': {'word': 'foo', 'times': 3}})
    assert res.output_value() == 'foofoofoo'


######

@solid(config_field=Field(Any))
def any_config(context):
    return context.solid_config


@solid(config_field=Field(Bool))
def bool_config(context):
    return 'true' if context.solid_config else 'false'


@solid(config_field=Field(Int))
def add_n(context, x: Int) -> int:
    return x + context.solid_config


@solid(config_field=Field(Float))
def div_y(context, x: Float) -> float:
    return x / context.solid_config


@solid(config_field=Field(float))
def div_y_var(context, x: Float) -> float:
    return x / context.solid_config


@solid(config_field=Field(String))
def hello(context) -> str:
    return 'Hello, {friend}!'.format(friend=context.solid_config)


@solid(config_field=Field(Path))
def unpickle(context) -> Any:
    with open(context.solid_config, 'rb') as fd:
        return pickle.load(fd)


@solid(config_field=Field(List[String]))
def concat_config(context) -> String:
    return ''.join(context.solid_config)


@solid(config_field=Field(Dict({'word': Field(String), 'times': Field(Int)})))
def repeat_config(context) -> str:
    return context.solid_config['word'] * context.solid_config['times']


def test_any_config():
    res = execute_solid(any_config, environment_dict={'solids': {'any_config': {'config': 'foo'}}})
    assert res.output_value() == 'foo'

    res = execute_solid(
        any_config, environment_dict={'solids': {'any_config': {'config': {'zip': 'zowie'}}}}
    )
    assert res.output_value() == {'zip': 'zowie'}


def test_bool_config():
    res = execute_solid(bool_config, environment_dict={'solids': {'bool_config': {'config': True}}})
    assert res.output_value() == 'true'

    res = execute_solid(bool_config, environment_dict={'solids': {'bool_config': {'config': False}}})
    assert res.output_value() == 'false'


def test_add_n():
    res = execute_solid(
        add_n, input_values={'x': 3}, environment_dict={'solids': {'add_n': {'config': 7}}}
    )
    assert res.output_value() == 10


def test_div_y():
    res = execute_solid(
        div_y, input_values={'x': 3.}, environment_dict={'solids': {'div_y': {'config': 2.}}}
    )
    assert res.output_value() == 1.5


def test_div_y_var():
    res = execute_solid(
        div_y_var, input_values={'x': 3.}, environment_dict={'solids': {'div_y_var': {'config': 2.}}}
    )
    assert res.output_value() == 1.5


def test_hello():
    res = execute_solid(hello, environment_dict={'solids': {'hello': {'config': 'Max'}}})
    assert res.output_value() == 'Hello, Max!'


def test_unpickle():
    with tempfile.NamedTemporaryFile() as fd:
        pickle.dump('foo', fd)
        fd.seek(0)
        res = execute_solid(unpickle, environment_dict={'solids': {'unpickle': {'config': fd.name}}})
        assert res.output_value() == 'foo'


def test_concat_config():
    res = execute_solid(
        concat_config,
        environment_dict={'solids': {'concat_config': {'config': ['foo', 'bar', 'baz']}}}
    )
    assert res.output_value() == 'foobarbaz'


def test_repeat_config():
    res = execute_solid(
        repeat_config,
        environment_dict={'solids': {'repeat_config': {'config': {'word': 'foo', 'times': 3}}}}
    )
    assert res.output_value() == 'foofoofoo'
