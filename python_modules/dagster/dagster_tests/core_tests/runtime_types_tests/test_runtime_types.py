import dagster as dg
import pytest
from dagster._core.types import dagster_type
from dagster._core.types.dagster_type import (
    ALL_RUNTIME_BUILTINS,
    DagsterTypeKind,
    resolve_dagster_type,
)


def inner_type_key_set(dagster_type):
    return {t.key for t in dagster_type.inner_types}


def test_inner_types():
    assert resolve_dagster_type(dg.Int).inner_types == []

    list_int_runtime = resolve_dagster_type(dg.List[dg.Int])
    assert inner_type_key_set(list_int_runtime) == set(["Int"])

    list_list_int_runtime = resolve_dagster_type(dg.List[dg.List[dg.Int]])
    assert inner_type_key_set(list_list_int_runtime) == set(["Int", "List.Int"])

    list_nullable_int_runtime = resolve_dagster_type(dg.List[dg.Optional[dg.Int]])
    assert inner_type_key_set(list_nullable_int_runtime) == set(["Int", "Optional.Int"])
    assert not list_nullable_int_runtime.kind == DagsterTypeKind.SCALAR

    tuple_optional_list = resolve_dagster_type(
        dg.Tuple[dg.List[dg.Optional[dg.Int]], dg.List[dg.Dict[str, str]]]
    )
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

    deep_dict = resolve_dagster_type(dg.Dict[str, dg.Dict[str, dg.Dict[str, int]]])
    assert inner_type_key_set(deep_dict) == set(
        [
            "TypedPythonDict.String.TypedPythonDict.String.Int",
            "TypedPythonDict.String.Int",
            "String",
            "Int",
        ]
    )

    deep_set = resolve_dagster_type(dg.Set[dg.Dict[str, dg.Dict[str, int]]])
    assert inner_type_key_set(deep_set) == set(
        [
            "TypedPythonDict.String.TypedPythonDict.String.Int",
            "TypedPythonDict.String.Int",
            "String",
            "Int",
        ]
    )


def test_is_any():
    assert not resolve_dagster_type(dg.Int).kind == DagsterTypeKind.ANY
    assert resolve_dagster_type(dg.Int).kind == DagsterTypeKind.SCALAR


def test_display_name():
    int_runtime = resolve_dagster_type(dg.Int)
    assert int_runtime.display_name == "Int"
    list_int_runtime = resolve_dagster_type(dg.List[dg.Int])
    assert list_int_runtime.display_name == "[Int]"
    list_list_int_runtime = resolve_dagster_type(dg.List[dg.List[dg.Int]])
    assert list_list_int_runtime.display_name == "[[Int]]"
    list_nullable_int_runtime = resolve_dagster_type(dg.List[dg.Optional[dg.Int]])
    assert list_nullable_int_runtime.display_name == "[Int?]"


def test_builtins_available():
    job_def = dg.GraphDefinition(name="test_builting_available", node_defs=[]).to_job()
    for builtin_type in ALL_RUNTIME_BUILTINS:
        assert builtin_type.unique_name is not None
        assert job_def.has_dagster_type(builtin_type.unique_name)
        assert job_def.dagster_type_named(builtin_type.unique_name).is_builtin


def test_python_mapping():
    runtime = resolve_dagster_type(int)
    assert runtime.unique_name == "Int"
    runtime = resolve_dagster_type(str)
    assert runtime.unique_name == "String"
    runtime = resolve_dagster_type(bool)
    assert runtime.unique_name == "Bool"
    runtime = resolve_dagster_type(float)
    assert runtime.unique_name == "Float"

    @dg.op(ins={"num": dg.In(int)})
    def add_one(num):
        return num + 1

    assert add_one.input_defs[0].dagster_type.unique_name == "Int"

    runtime = resolve_dagster_type(float)
    runtime.type_check(None, 1.0)  # ty: ignore[invalid-argument-type]
    res = runtime.type_check(None, 1)  # ty: ignore[invalid-argument-type]
    assert not res.success

    runtime = resolve_dagster_type(bool)
    runtime.type_check(None, True)  # ty: ignore[invalid-argument-type]
    res = runtime.type_check(None, 1)  # ty: ignore[invalid-argument-type]
    assert not res.success


def test_double_dagster_type():
    AlwaysSucceedsFoo = dg.DagsterType(name="Foo", type_check_fn=lambda _, _val: True)
    AlwaysFailsFoo = dg.DagsterType(name="Foo", type_check_fn=lambda _, _val: False)

    @dg.op
    def return_a_thing():
        return 1

    @dg.op(
        ins={"succeeds": dg.In(AlwaysSucceedsFoo)},
        out=dg.Out(AlwaysFailsFoo),
    )
    def yup(succeeds):
        return succeeds

    with pytest.raises(dg.DagsterInvalidDefinitionError) as exc_info:

        @dg.job
        def _should_fail():
            yup(return_a_thing())

    assert (
        str(exc_info.value) == 'You have created two dagster types with the same name "Foo". '
        "Dagster types have must have unique names."
    )


def test_comparison():
    # Base types
    assert resolve_dagster_type(dg.Any) == resolve_dagster_type(dg.Any)
    assert resolve_dagster_type(dg.String) == resolve_dagster_type(dg.String)
    assert resolve_dagster_type(dg.Bool) == resolve_dagster_type(dg.Bool)
    assert resolve_dagster_type(dg.Float) == resolve_dagster_type(dg.Float)
    assert resolve_dagster_type(dg.Int) == resolve_dagster_type(dg.Int)
    assert resolve_dagster_type(dg.String) == resolve_dagster_type(dg.String)
    assert resolve_dagster_type(dg.Nothing) == resolve_dagster_type(dg.Nothing)
    assert resolve_dagster_type(dg.Optional[dg.String]) == resolve_dagster_type(
        dg.Optional[dg.String]
    )

    types = [dg.Any, dg.Bool, dg.Float, dg.Int, dg.String, dg.Nothing]
    non_equal_pairs = [(t1, t2) for t1 in types for t2 in types if t1 != t2]
    for t1, t2 in non_equal_pairs:
        assert resolve_dagster_type(t1) != resolve_dagster_type(t2)
    assert resolve_dagster_type(dg.Optional[dg.String]) != resolve_dagster_type(dg.Optional[dg.Int])

    # List type
    assert resolve_dagster_type(dg.List) == resolve_dagster_type(dg.List)
    assert resolve_dagster_type(dg.List[dg.String]) == resolve_dagster_type(dg.List[dg.String])
    assert resolve_dagster_type(dg.List[dg.List[dg.Int]]) == resolve_dagster_type(
        dg.List[dg.List[dg.Int]]
    )
    assert resolve_dagster_type(dg.List[dg.Optional[dg.String]]) == resolve_dagster_type(
        dg.List[dg.Optional[dg.String]]
    )

    assert resolve_dagster_type(dg.List[dg.String]) != resolve_dagster_type(dg.List[dg.Int])
    assert resolve_dagster_type(dg.List[dg.List[dg.String]]) != resolve_dagster_type(
        dg.List[dg.List[dg.Int]]
    )
    assert resolve_dagster_type(dg.List[dg.String]) != resolve_dagster_type(
        dg.List[dg.Optional[dg.String]]
    )

    # Tuple type
    assert resolve_dagster_type(dg.Tuple) == resolve_dagster_type(dg.Tuple)
    assert resolve_dagster_type(dg.Tuple[dg.String, dg.Int]) == resolve_dagster_type(
        dg.Tuple[dg.String, dg.Int]
    )
    assert resolve_dagster_type(dg.Tuple[dg.Tuple[dg.String, dg.Int]]) == resolve_dagster_type(
        dg.Tuple[dg.Tuple[dg.String, dg.Int]]
    )
    assert resolve_dagster_type(dg.Tuple[dg.Optional[dg.String], dg.Int]) == resolve_dagster_type(
        dg.Tuple[dg.Optional[dg.String], dg.Int]
    )

    assert resolve_dagster_type(dg.Tuple[dg.String, dg.Int]) != resolve_dagster_type(
        dg.Tuple[dg.Int, dg.String]
    )
    assert resolve_dagster_type(dg.Tuple[dg.Tuple[dg.String, dg.Int]]) != resolve_dagster_type(
        dg.Tuple[dg.Tuple[dg.Int, dg.String]]
    )
    assert resolve_dagster_type(dg.Tuple[dg.String]) != resolve_dagster_type(
        dg.Tuple[dg.Optional[dg.String]]
    )

    # Set type
    assert resolve_dagster_type(dg.Set) == resolve_dagster_type(dg.Set)
    assert resolve_dagster_type(dg.Set[dg.String]) == resolve_dagster_type(dg.Set[dg.String])
    assert resolve_dagster_type(dg.Set[dg.Set[dg.Int]]) == resolve_dagster_type(
        dg.Set[dg.Set[dg.Int]]
    )
    assert resolve_dagster_type(dg.Set[dg.Optional[dg.String]]) == resolve_dagster_type(
        dg.Set[dg.Optional[dg.String]]
    )

    assert resolve_dagster_type(dg.Set[dg.String]) != resolve_dagster_type(dg.Set[dg.Int])
    assert resolve_dagster_type(dg.Set[dg.Set[dg.String]]) != resolve_dagster_type(
        dg.Set[dg.Set[dg.Int]]
    )
    assert resolve_dagster_type(dg.Set[dg.String]) != resolve_dagster_type(
        dg.Set[dg.Optional[dg.String]]
    )

    # Dict type
    assert resolve_dagster_type(dg.Dict) == resolve_dagster_type(dg.Dict)
    assert resolve_dagster_type(dg.Dict[dg.String, dg.Int]) == resolve_dagster_type(
        dg.Dict[dg.String, dg.Int]
    )
    assert resolve_dagster_type(
        dg.Dict[dg.String, dg.Dict[dg.String, dg.Int]]
    ) == resolve_dagster_type(dg.Dict[dg.String, dg.Dict[dg.String, dg.Int]])

    assert resolve_dagster_type(dg.Dict[dg.String, dg.Int]) != resolve_dagster_type(
        dg.Dict[dg.Int, dg.String]
    )
    assert resolve_dagster_type(
        dg.Dict[dg.Int, dg.Dict[dg.String, dg.Int]]
    ) != resolve_dagster_type(dg.Dict[dg.String, dg.Dict[dg.String, dg.Int]])


def test_resolve_dagster_type_is_memoized(monkeypatch: pytest.MonkeyPatch):
    class SomeClass:
        pass

    for annotation in (int, str, None, dg.Int, list[int], dict[str, int], SomeClass):
        first = resolve_dagster_type(annotation)
        assert annotation is None or annotation in dagster_type._RESOLVE_DAGSTER_TYPE_CACHE  # noqa: SLF001
        assert resolve_dagster_type(annotation) is first

    # Cache hits skip the uncached resolution path entirely.
    def unexpected_resolution(_: object) -> dg.DagsterType:
        pytest.fail("Expected a memoized result")

    monkeypatch.setattr(dagster_type, "_resolve_dagster_type_uncached", unexpected_resolution)
    assert resolve_dagster_type(list[int]) is resolve_dagster_type(list[int])
    assert resolve_dagster_type(SomeClass).typing_type is SomeClass


def test_resolve_dagster_type_does_not_cache_failures():
    # Unhashable inputs (e.g. an instance where a type was meant) still raise.
    for _ in range(2):
        with pytest.raises(dg.DagsterInvalidDefinitionError, match="hashable"):
            resolve_dagster_type({"not": "a type"})

    # Hashable but invalid inputs raise on every call and are not cached.
    for _ in range(2):
        with pytest.raises(dg.DagsterInvalidDefinitionError):
            resolve_dagster_type("not a type")
    assert "not a type" not in dagster_type._RESOLVE_DAGSTER_TYPE_CACHE  # noqa: SLF001


def test_resolve_dagster_type_does_not_conflate_equal_dagster_types():
    # DagsterType equality is by key, so two distinct types with the same name compare equal.
    # Neither the types themselves nor annotations embedding them may be served from the cache.
    foo_a = dg.DagsterType(name="Foo", type_check_fn=lambda _, _v: True)
    foo_b = dg.DagsterType(name="Foo", type_check_fn=lambda _, _v: False)
    assert foo_a == foo_b
    assert resolve_dagster_type(foo_a) is foo_a
    assert resolve_dagster_type(foo_b) is foo_b

    assert list[foo_a] == list[foo_b]
    assert resolve_dagster_type(list[foo_a]).inner_types[0] is foo_a
    assert resolve_dagster_type(list[foo_b]).inner_types[0] is foo_b
    assert resolve_dagster_type(list[foo_b] | None).inner_types[0].inner_types[0] is foo_b
    assert list[foo_a] not in dagster_type._RESOLVE_DAGSTER_TYPE_CACHE  # noqa: SLF001
