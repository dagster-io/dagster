from dagster import List, Optional, Int, PipelineDefinition, InputDefinition, lambda_solid

from dagster.core.types.runtime import resolve_to_runtime_type, ALL_RUNTIME_BUILTINS


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
    int_runtime = resolve_to_runtime_type(int)
    assert int_runtime.name == 'Int'
    int_runtime = resolve_to_runtime_type(str)
    assert int_runtime.name == 'String'
    int_runtime = resolve_to_runtime_type(bool)
    assert int_runtime.name == 'Bool'
    int_runtime = resolve_to_runtime_type(float)
    assert int_runtime.name == 'Float'

    @lambda_solid(input_defs=[InputDefinition('num', int)])
    def add_one(num):
        return num + 1

    assert add_one.input_defs[0].runtime_type.name == 'Int'
