from typing import Annotated, Optional, Sequence

import pytest
from dagster_components.core.component_rendering import (
    RenderedModel,
    RenderingMetadata,
    TemplatedValueRenderer,
    can_render_with_default_scope,
)
from pydantic import BaseModel, TypeAdapter, ValidationError


class InnerRendered(RenderedModel):
    a: Optional[str] = None


class Container(BaseModel):
    a: str
    inner: InnerRendered


class Outer(BaseModel):
    a: str
    inner: InnerRendered
    container: Container
    container_optional: Optional[Container] = None
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
def test_can_render(path, expected: bool) -> None:
    assert (
        can_render_with_default_scope(path, Outer.model_json_schema(), Outer.model_json_schema())
        == expected
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

    renderer = TemplatedValueRenderer(context={"foo_val": "foo", "bar_val": "bar"})
    rendered_data = renderer.render_params(data, Outer)

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


class RM(RenderedModel):
    the_renderable_int: Annotated[str, RenderingMetadata(output_type=int)]
    the_unrenderable_int: int

    the_str: str
    the_opt_int: Annotated[Optional[str], RenderingMetadata(output_type=Optional[int])] = None


def test_valid_rendering() -> None:
    rm = RM(
        the_renderable_int="{{ some_int }}",
        the_unrenderable_int=1,
        the_str="{{ some_str }}",
        the_opt_int="{{ some_int }}",
    )
    renderer = TemplatedValueRenderer(context={"some_int": 1, "some_str": "aaa"})
    resolved_properties = rm.render_properties(renderer)

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

    renderer = TemplatedValueRenderer(context={"some_int": 1, "some_str": "aaa"})

    with pytest.raises(ValidationError):
        # string is not a valid output type for the_opt_int
        rm.render_properties(renderer)
