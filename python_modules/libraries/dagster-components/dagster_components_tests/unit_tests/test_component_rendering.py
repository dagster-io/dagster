from typing import Optional, Sequence

import pytest
from dagster_components.core.component_rendering import (
    TemplatedValueResolver,
    _should_render,
    add_required_rendering_context,
    preprocess_value,
)
from pydantic import BaseModel, Field, TypeAdapter


class Inner(BaseModel):
    a: Optional[str] = None
    deferred: Optional[str] = add_required_rendering_context(
        Field(default=None), {"foo", "bar", "baz"}
    )


class Outer(BaseModel):
    a: str
    deferred: str = add_required_rendering_context(Field(), {"a"})
    inner: Sequence[Inner]
    inner_deferred: Sequence[Inner] = add_required_rendering_context(Field(), {"b"})

    inner_optional: Optional[Sequence[Inner]] = None
    inner_deferred_optional: Optional[Sequence[Inner]] = add_required_rendering_context(
        Field(default=None), {"b"}
    )


@pytest.mark.parametrize(
    "path,expected",
    [
        (["a"], True),
        (["deferred"], False),
        (["inner", 0, "a"], True),
        (["inner", 0, "deferred"], False),
        (["inner_deferred", 0, "a"], False),
        (["inner_deferred", 0, "deferred"], False),
        (["inner_optional"], True),
        (["inner_optional", 0, "a"], True),
        (["inner_optional", 0, "deferred"], False),
        (["inner_deferred_optional", 0], False),
        (["inner_deferred_optional", 0, "a"], False),
        (["NONEXIST", 0, "deferred"], False),
    ],
)
def test_should_render(path, expected: bool) -> None:
    assert _should_render(path, Outer.model_json_schema(), Outer.model_json_schema()) == expected


def test_render() -> None:
    data = {
        "a": "{{ foo_val }}",
        "deferred": "{{ deferred }}",
        "inner": [
            {"a": "{{ bar_val }}", "deferred": "{{ deferred }}"},
            {"a": "zzz", "deferred": "zzz"},
        ],
        "inner_deferred": [
            {"a": "{{ deferred }}", "deferred": "zzz"},
        ],
    }

    renderer = TemplatedValueResolver(context={"foo_val": "foo", "bar_val": "bar"})
    rendered_data = preprocess_value(renderer, data, Outer)

    assert rendered_data == {
        "a": "foo",
        "deferred": "{{ deferred }}",
        "inner": [
            {"a": "bar", "deferred": "{{ deferred }}"},
            {"a": "zzz", "deferred": "zzz"},
        ],
        "inner_deferred": [
            {"a": "{{ deferred }}", "deferred": "zzz"},
        ],
    }

    TypeAdapter(Outer).validate_python(rendered_data)
