import pytest

from dagster import (
    DagsterInvalidDefinitionError,
    InputDefinition,
    Int,
    List,
    Optional,
    OutputDefinition,
    PipelineDefinition,
    lambda_solid,
    pipeline,
)
from dagster.core.types.runtime_type import (
    ALL_RUNTIME_BUILTINS,
    RuntimeType,
    resolve_to_runtime_type,
)


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
    pipeline_def = PipelineDefinition(name='test_builting_available', solid_defs=[])
    for builtin_type in ALL_RUNTIME_BUILTINS:
        assert pipeline_def.has_runtime_type(builtin_type.name)
        assert pipeline_def.runtime_type_named(builtin_type.name).is_builtin


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
    res = runtime.type_check(1)
    assert not res.success

    runtime = resolve_to_runtime_type(bool)
    runtime.type_check(True)
    res = runtime.type_check(1)
    assert not res.success


def test_double_runtime_type():

    AlwaysSucceedsFoo = RuntimeType('Foo', 'Foo', type_check_fn=lambda _: True)
    AlwaysFailsFoo = RuntimeType('Foo', 'Foo', type_check_fn=lambda _: False)

    @lambda_solid
    def return_a_thing():
        return 1

    @lambda_solid(
        input_defs=[InputDefinition('succeeds', AlwaysSucceedsFoo)],
        output_def=OutputDefinition(AlwaysFailsFoo),
    )
    def yup(succeeds):
        return succeeds

    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:

        @pipeline
        def _should_fail():
            yup(return_a_thing())

    assert str(exc_info.value) == (
        'You have created two dagster types with the same name "Foo". '
        'Dagster types have must have unique names.'
    )
