from collections.abc import Sequence, Set
from typing import Annotated, Optional

import pytest
from dagster_components import ComponentSchemaBaseModel, ResolvableFieldInfo, TemplatedValueResolver
from dagster_components.core.schema.metadata import allow_resolve, get_available_scope
from pydantic import BaseModel, Field, TypeAdapter, ValidationError


class InnerRendered(ComponentSchemaBaseModel):
    a: Optional[str] = None


class Container(BaseModel):
    a: str
    inner: InnerRendered
    inner_scoped: Annotated[InnerRendered, ResolvableFieldInfo(additional_scope={"c", "d"})] = (
        Field(default_factory=InnerRendered)
    )


class Outer(BaseModel):
    a: str
    inner: InnerRendered
    container: Container
    container_optional: Optional[Container] = None
    container_optional_scoped: Annotated[
        Optional[Container], ResolvableFieldInfo(additional_scope={"a", "b"})
    ] = None
    inner_seq: Sequence[InnerRendered]
    inner_optional: Optional[InnerRendered] = None
    inner_optional_seq: Optional[Sequence[InnerRendered]] = None


@pytest.mark.parametrize(
    "path,expected",
    [
        (["a"], True),
        (["inner"], False),
        (["inner", "a"], False),
        (["container", "a"], True),
        (["container", "inner"], False),
        (["container", "inner", "a"], False),
        (["container_optional", "a"], True),
        (["container_optional", "inner"], False),
        (["container_optional", "inner", "a"], False),
        (["container_optional_scoped"], False),
        (["container_optional_scoped", "inner", "a"], False),
        (["container_optional_scoped", "inner_scoped", "a"], False),
        (["inner_seq"], True),
        (["inner_seq", 0], False),
        (["inner_seq", 0, "a"], False),
        (["inner_optional"], True),
        (["inner_optional", "a"], False),
        (["inner_optional_seq"], True),
        (["inner_optional_seq", 0], False),
        (["inner_optional_seq", 0, "a"], False),
    ],
)
def test_allow_render(path, expected: bool) -> None:
    assert allow_resolve(path, Outer.model_json_schema(), Outer.model_json_schema()) == expected


@pytest.mark.parametrize(
    "path,expected",
    [
        (["a"], set()),
        (["inner", "a"], set()),
        (["container_optional", "inner", "a"], set()),
        (["inner_seq"], set()),
        (["container_optional_scoped"], {"a", "b"}),
        (["container_optional_scoped", "inner"], {"a", "b"}),
        (["container_optional_scoped", "inner_scoped"], {"a", "b", "c", "d"}),
        (["container_optional_scoped", "inner_scoped", "a"], {"a", "b", "c", "d"}),
    ],
)
def test_get_available_scope(path, expected: Set[str]) -> None:
    assert (
        get_available_scope(path, Outer.model_json_schema(), Outer.model_json_schema()) == expected
    )


def test_render() -> None:
    data = {
        "a": "{{ foo_val }}",
        "inner": {"a": "{{ deferred }}"},
        "inner_seq": [
            {"a": "{{ deferred }}"},
        ],
        "container": {
            "a": "{{ bar_val }}",
            "inner": {"a": "{{ deferred }}"},
        },
    }

    renderer = TemplatedValueResolver(scope={"foo_val": "foo", "bar_val": "bar"})
    rendered_data = renderer.resolve_params(data, Outer)

    assert rendered_data == {
        "a": "foo",
        "inner": {"a": "{{ deferred }}"},
        "inner_seq": [
            {"a": "{{ deferred }}"},
        ],
        "container": {
            "a": "bar",
            "inner": {"a": "{{ deferred }}"},
        },
    }

    TypeAdapter(Outer).validate_python(rendered_data)


class RM(ComponentSchemaBaseModel):
    the_renderable_int: Annotated[str, ResolvableFieldInfo(output_type=int)]
    the_unrenderable_int: int

    the_str: str
    the_opt_int: Annotated[Optional[str], ResolvableFieldInfo(output_type=Optional[int])] = None


def test_valid_rendering() -> None:
    rm = RM(
        the_renderable_int="{{ some_int }}",
        the_unrenderable_int=1,
        the_str="{{ some_str }}",
        the_opt_int="{{ some_int }}",
    )
    renderer = TemplatedValueResolver(scope={"some_int": 1, "some_str": "aaa"})
    resolved_properties = rm.resolve_properties(renderer)

    assert resolved_properties == {
        "the_renderable_int": 1,
        "the_unrenderable_int": 1,
        "the_str": "aaa",
        "the_opt_int": 1,
    }


def test_invalid_rendering() -> None:
    rm = RM(
        the_renderable_int="{{ some_int }}",
        the_unrenderable_int=1,
        the_str="{{ some_str }}",
        the_opt_int="{{ some_str }}",
    )

    renderer = TemplatedValueResolver(scope={"some_int": 1, "some_str": "aaa"})

    with pytest.raises(ValidationError):
        # string is not a valid output type for the_opt_int
        rm.resolve_properties(renderer)
