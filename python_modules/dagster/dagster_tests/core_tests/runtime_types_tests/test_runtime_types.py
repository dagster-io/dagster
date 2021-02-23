import pytest
from dagster import (
    Any,
    Bool,
    DagsterInvalidDefinitionError,
    Dict,
    Float,
    InputDefinition,
    Int,
    List,
    Nothing,
    Optional,
    OutputDefinition,
    PipelineDefinition,
    Set,
    String,
    Tuple,
    lambda_solid,
    pipeline,
)
from dagster.core.types.dagster_type import (
    ALL_RUNTIME_BUILTINS,
    DagsterType,
    DagsterTypeKind,
    resolve_dagster_type,
)


def inner_type_key_set(dagster_type):
    return {t.key for t in dagster_type.inner_types}


def test_inner_types():
    assert resolve_dagster_type(Int).inner_types == []

    list_int_runtime = resolve_dagster_type(List[Int])
    assert inner_type_key_set(list_int_runtime) == set(["Int"])

    list_list_int_runtime = resolve_dagster_type(List[List[Int]])
    assert inner_type_key_set(list_list_int_runtime) == set(["Int", "List.Int"])

    list_nullable_int_runtime = resolve_dagster_type(List[Optional[Int]])
    assert inner_type_key_set(list_nullable_int_runtime) == set(["Int", "Optional.Int"])
    assert not list_nullable_int_runtime.kind == DagsterTypeKind.SCALAR

    tuple_optional_list = resolve_dagster_type(Tuple[List[Optional[Int]], List[Dict[str, str]]])
    assert inner_type_key_set(tuple_optional_list) == set(
        [
            "Int",
            "Optional.Int",
            "List.Optional.Int",
            "String",
            "TypedPythonDict.String.String",
            "List.TypedPythonDict.String.String",
        ]
    )
    assert not tuple_optional_list.kind == DagsterTypeKind.SCALAR


def test_is_any():
    assert not resolve_dagster_type(Int).kind == DagsterTypeKind.ANY
    assert resolve_dagster_type(Int).kind == DagsterTypeKind.SCALAR


def test_display_name():

    int_runtime = resolve_dagster_type(Int)
    assert int_runtime.display_name == "Int"
    list_int_runtime = resolve_dagster_type(List[Int])
    assert list_int_runtime.display_name == "[Int]"
    list_list_int_runtime = resolve_dagster_type(List[List[Int]])
    assert list_list_int_runtime.display_name == "[[Int]]"
    list_nullable_int_runtime = resolve_dagster_type(List[Optional[Int]])
    assert list_nullable_int_runtime.display_name == "[Int?]"


def test_builtins_available():
    pipeline_def = PipelineDefinition(name="test_builting_available", solid_defs=[])
    for builtin_type in ALL_RUNTIME_BUILTINS:
        assert pipeline_def.has_dagster_type(builtin_type.unique_name)
        assert pipeline_def.dagster_type_named(builtin_type.unique_name).is_builtin


def test_python_mapping():
    runtime = resolve_dagster_type(int)
    assert runtime.unique_name == "Int"
    runtime = resolve_dagster_type(str)
    assert runtime.unique_name == "String"
    runtime = resolve_dagster_type(bool)
    assert runtime.unique_name == "Bool"
    runtime = resolve_dagster_type(float)
    assert runtime.unique_name == "Float"

    @lambda_solid(input_defs=[InputDefinition("num", int)])
    def add_one(num):
        return num + 1

    assert add_one.input_defs[0].dagster_type.unique_name == "Int"

    runtime = resolve_dagster_type(float)
    runtime.type_check(None, 1.0)
    res = runtime.type_check(None, 1)
    assert not res.success

    runtime = resolve_dagster_type(bool)
    runtime.type_check(None, True)
    res = runtime.type_check(None, 1)
    assert not res.success


def test_double_dagster_type():

    AlwaysSucceedsFoo = DagsterType(name="Foo", type_check_fn=lambda _, _val: True)
    AlwaysFailsFoo = DagsterType(name="Foo", type_check_fn=lambda _, _val: False)

    @lambda_solid
    def return_a_thing():
        return 1

    @lambda_solid(
        input_defs=[InputDefinition("succeeds", AlwaysSucceedsFoo)],
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
        "Dagster types have must have unique names."
    )


def test_comparison():
    # Base types
    assert resolve_dagster_type(Any) == resolve_dagster_type(Any)
    assert resolve_dagster_type(String) == resolve_dagster_type(String)
    assert resolve_dagster_type(Bool) == resolve_dagster_type(Bool)
    assert resolve_dagster_type(Float) == resolve_dagster_type(Float)
    assert resolve_dagster_type(Int) == resolve_dagster_type(Int)
    assert resolve_dagster_type(String) == resolve_dagster_type(String)
    assert resolve_dagster_type(Nothing) == resolve_dagster_type(Nothing)
    assert resolve_dagster_type(Optional[String]) == resolve_dagster_type(Optional[String])

    types = [Any, Bool, Float, Int, String, Nothing]
    non_equal_pairs = [(t1, t2) for t1 in types for t2 in types if t1 != t2]
    for t1, t2 in non_equal_pairs:
        assert resolve_dagster_type(t1) != resolve_dagster_type(t2)
    assert resolve_dagster_type(Optional[String]) != resolve_dagster_type(Optional[Int])

    # List type
    assert resolve_dagster_type(List) == resolve_dagster_type(List)
    assert resolve_dagster_type(List[String]) == resolve_dagster_type(List[String])
    assert resolve_dagster_type(List[List[Int]]) == resolve_dagster_type(List[List[Int]])
    assert resolve_dagster_type(List[Optional[String]]) == resolve_dagster_type(
        List[Optional[String]]
    )

    assert resolve_dagster_type(List[String]) != resolve_dagster_type(List[Int])
    assert resolve_dagster_type(List[List[String]]) != resolve_dagster_type(List[List[Int]])
    assert resolve_dagster_type(List[String]) != resolve_dagster_type(List[Optional[String]])

    # Tuple type
    assert resolve_dagster_type(Tuple) == resolve_dagster_type(Tuple)
    assert resolve_dagster_type(Tuple[String, Int]) == resolve_dagster_type(Tuple[String, Int])
    assert resolve_dagster_type(Tuple[Tuple[String, Int]]) == resolve_dagster_type(
        Tuple[Tuple[String, Int]]
    )
    assert resolve_dagster_type(Tuple[Optional[String], Int]) == resolve_dagster_type(
        Tuple[Optional[String], Int]
    )

    assert resolve_dagster_type(Tuple[String, Int]) != resolve_dagster_type(Tuple[Int, String])
    assert resolve_dagster_type(Tuple[Tuple[String, Int]]) != resolve_dagster_type(
        Tuple[Tuple[Int, String]]
    )
    assert resolve_dagster_type(Tuple[String]) != resolve_dagster_type(Tuple[Optional[String]])

    # Set type
    assert resolve_dagster_type(Set) == resolve_dagster_type(Set)
    assert resolve_dagster_type(Set[String]) == resolve_dagster_type(Set[String])
    assert resolve_dagster_type(Set[Set[Int]]) == resolve_dagster_type(Set[Set[Int]])
    assert resolve_dagster_type(Set[Optional[String]]) == resolve_dagster_type(
        Set[Optional[String]]
    )

    assert resolve_dagster_type(Set[String]) != resolve_dagster_type(Set[Int])
    assert resolve_dagster_type(Set[Set[String]]) != resolve_dagster_type(Set[Set[Int]])
    assert resolve_dagster_type(Set[String]) != resolve_dagster_type(Set[Optional[String]])

    # Dict type
    assert resolve_dagster_type(Dict) == resolve_dagster_type(Dict)
    assert resolve_dagster_type(Dict[String, Int]) == resolve_dagster_type(Dict[String, Int])
    assert resolve_dagster_type(Dict[String, Dict[String, Int]]) == resolve_dagster_type(
        Dict[String, Dict[String, Int]]
    )

    assert resolve_dagster_type(Dict[String, Int]) != resolve_dagster_type(Dict[Int, String])
    assert resolve_dagster_type(Dict[Int, Dict[String, Int]]) != resolve_dagster_type(
        Dict[String, Dict[String, Int]]
    )
