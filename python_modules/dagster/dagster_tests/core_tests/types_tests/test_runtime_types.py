from dagster import List, Nullable, Int, PipelineDefinition

from dagster.core.types.runtime import resolve_to_runtime_type, ALL_RUNTIME_BUILTINS


def inner_type_key_set(runtime_type):
    return {t.key for t in runtime_type.inner_types}


def test_inner_types():
    assert resolve_to_runtime_type(Int).inner_types == []

    list_int_runtime = resolve_to_runtime_type(List(Int))
    assert inner_type_key_set(list_int_runtime) == set(['Int'])

    list_list_int_runtime = resolve_to_runtime_type(List(List(Int)))
    assert inner_type_key_set(list_list_int_runtime) == set(['Int', 'List.Int'])

    list_nullable_int_runtime = resolve_to_runtime_type(List(Nullable(Int)))
    assert inner_type_key_set(list_nullable_int_runtime) == set(['Int', 'Nullable.Int'])


def test_display_name():

    int_runtime = resolve_to_runtime_type(Int)
    assert int_runtime.display_name == 'Int'
    list_int_runtime = resolve_to_runtime_type(List(Int))
    assert list_int_runtime.display_name == '[Int]'
    list_list_int_runtime = resolve_to_runtime_type(List(List(Int)))
    assert list_list_int_runtime.display_name == '[[Int]]'
    list_nullable_int_runtime = resolve_to_runtime_type(List(Nullable(Int)))
    assert list_nullable_int_runtime.display_name == '[Int?]'


def test_builtins_available():
    pipeline = PipelineDefinition(name='test_builting_available', solids=[])
    for builtin_type in ALL_RUNTIME_BUILTINS:
        assert pipeline.has_runtime_type(builtin_type.name)
        assert pipeline.runtime_type_named(builtin_type.name).is_builtin
