import pytest

from dagster import Failure, InputDefinition, Int, lambda_solid, List, Optional, PipelineDefinition
from dagster.core.types.runtime import ALL_RUNTIME_BUILTINS, resolve_to_runtime_type


def inner_type_key_set(runtime_type):
    return {t.key for t in runtime_type.inner_types}


def test_inner_types():
    assert resolve_to_runtime_type(Int).inner_types == []

    list_int_runtime = resolve_to_runtime_type(List[Int])
    assert inner_type_key_set(list_int_runtime) == set(['Int'])

    list_list_int_runtime = resolve_to_runtime_type(List[List[Int]])
    assert inner_type_key_set(list_list_int_runtime) == set(['Int', 'List.Int'])

    list_nullable_int_runtime = resolve_to_runtime_type(List[Optional[Int]])
    assert inner_type_key_set(list_nullable_int_runtime) == set(['Int', 'Optional.Int'])
    assert not list_nullable_int_runtime.is_scalar


def test_is_any():
    assert not resolve_to_runtime_type(Int).is_any
    assert resolve_to_runtime_type(Int).is_scalar


def test_display_name():

    int_runtime = resolve_to_runtime_type(Int)
    assert int_runtime.display_name == 'Int'
    list_int_runtime = resolve_to_runtime_type(List[Int])
    assert list_int_runtime.display_name == '[Int]'
    list_list_int_runtime = resolve_to_runtime_type(List[List[Int]])
    assert list_list_int_runtime.display_name == '[[Int]]'
    list_nullable_int_runtime = resolve_to_runtime_type(List[Optional[Int]])
    assert list_nullable_int_runtime.display_name == '[Int?]'


def test_builtins_available():
    pipeline = PipelineDefinition(name='test_builting_available', solid_defs=[])
    for builtin_type in ALL_RUNTIME_BUILTINS:
        assert pipeline.has_runtime_type(builtin_type.name)
        assert pipeline.runtime_type_named(builtin_type.name).is_builtin


def test_python_mapping():
    runtime = resolve_to_runtime_type(int)
    assert runtime.name == 'Int'
    runtime = resolve_to_runtime_type(str)
    assert runtime.name == 'String'
    runtime = resolve_to_runtime_type(bool)
    assert runtime.name == 'Bool'
    runtime = resolve_to_runtime_type(float)
    assert runtime.name == 'Float'

    @lambda_solid(input_defs=[InputDefinition('num', int)])
    def add_one(num):
        return num + 1

    assert add_one.input_defs[0].runtime_type.name == 'Int'

    runtime = resolve_to_runtime_type(float)
    runtime.type_check(1.0)
    with pytest.raises(Failure):
        runtime.type_check(1)

    runtime = resolve_to_runtime_type(bool)
    runtime.type_check(True)
    with pytest.raises(Failure):
        runtime.type_check(1)
