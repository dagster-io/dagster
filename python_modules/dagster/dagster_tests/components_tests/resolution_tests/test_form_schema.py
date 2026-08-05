"""Tests for the server-side raw-schema -> (dataSchema, uiSchema) split.

This is the Python decode side of the conventions the resolved framework emits
(``ui:*`` hints, ``__DAGSTER_UNSET_DEFAULT__`` sentinels, and the ``| str``
Jinja escape-hatch ``anyOf`` variants). It replaces the equivalent TypeScript
``schemaPrep.ts`` so encode and decode stay co-located.
"""

from dataclasses import dataclass
from typing import Annotated

import dagster as dg
from dagster.components.resolved.form_config import (
    APP_MANAGED,
    UNSET_DEFAULT_SENTINEL,
    ComponentFormConfig,
)
from dagster.components.resolved.form_schema import split_form_schema
from dagster.components.resolved.model import Resolver


def test_non_object_input():
    assert split_form_schema(None) == ({}, {})
    assert split_form_schema("nope") == ({}, {})
    assert split_form_schema(42) == ({}, {})


def test_lifts_ui_keys_into_ui_schema():
    raw = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "ui:placeholder": "e.g. my_job", "title": "Name"},
        },
    }
    data, ui = split_form_schema(raw)
    # ui:* keys are stripped from the data schema...
    assert data["properties"]["name"] == {"type": "string", "title": "Name"}
    # ...and lifted into the parallel uiSchema.
    assert ui == {"name": {"ui:placeholder": "e.g. my_job"}}


def test_strips_unset_default_sentinel():
    raw = {
        "type": "object",
        "properties": {
            "with_sentinel": {"type": "string", "default": UNSET_DEFAULT_SENTINEL},
            "with_real_default": {"type": "string", "default": "keep me"},
        },
    }
    data, _ = split_form_schema(raw)
    assert "default" not in data["properties"]["with_sentinel"]
    assert data["properties"]["with_real_default"]["default"] == "keep me"


def test_filters_jinja_string_escape_hatch():
    # A field made injectable becomes anyOf: [<real>, {type: "string"}]. The
    # escape hatch is filtered and the single surviving variant collapses into
    # the parent so the form renders a plain field, not a variant picker.
    raw = {
        "type": "object",
        "properties": {
            "count": {"anyOf": [{"type": "integer"}, {"type": "string"}]},
        },
    }
    data, _ = split_form_schema(raw)
    assert data["properties"]["count"] == {"type": "integer"}


def test_drops_null_variant_and_collapses_optional():
    # ``X | None`` optionals: the null variant encodes optionality already
    # expressed by the field being non-required, so it's dropped and the real
    # variant collapses into the parent. A null default is dropped with it.
    raw = {
        "type": "object",
        "properties": {
            "cron": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "default": None,
                "title": "Cron",
                "description": "keep me",
            },
        },
    }
    data, _ = split_form_schema(raw)
    cron = data["properties"]["cron"]
    assert cron == {"type": "string", "title": "Cron", "description": "keep me"}


def test_multi_variant_union_survives_null_drop():
    raw = {
        "anyOf": [
            {"type": "object", "properties": {"a": {"type": "string"}}},
            {"type": "object", "properties": {"b": {"type": "string"}}},
            {"type": "null"},
        ],
    }
    data, _ = split_form_schema(raw)
    assert len(data["anyOf"]) == 2
    assert all(v["type"] == "object" for v in data["anyOf"])


def test_collapse_lifts_ui_hints_from_variant():
    # A ``multiline`` hint on an Optional[str] lands inside the string variant;
    # the collapse must lift it to the field's ui node (previously this crashed
    # the form renderer with "No widget 'textarea'").
    raw = {
        "type": "object",
        "properties": {
            "notes": {
                "anyOf": [{"type": "string", "ui:widget": "textarea"}, {"type": "null"}],
                "default": None,
            },
        },
    }
    data, ui = split_form_schema(raw)
    assert data["properties"]["notes"] == {"type": "string"}
    assert ui["notes"] == {"ui:widget": "textarea"}


def test_lifts_ui_order():
    raw = {
        "type": "object",
        "ui:order": ["b", "a"],
        "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
    }
    data, ui = split_form_schema(raw)
    assert "ui:order" not in data
    assert ui["ui:order"] == ["b", "a"]


def test_keeps_genuine_string_only_anyof():
    # No "richer" variant (every variant is a bare-ish string) -> leave them all
    # untouched, matching schemaPrep.ts. A non-string variant like {type: null}
    # *would* count as richer and trigger filtering of the bare string.
    raw = {"anyOf": [{"type": "string", "format": "email"}, {"type": "string"}]}
    data, _ = split_form_schema(raw)
    assert data["anyOf"] == [{"type": "string", "format": "email"}, {"type": "string"}]


def test_collapses_single_const_anyof_and_hides_discriminator():
    raw = {
        "type": "object",
        "properties": {
            "kind": {"anyOf": [{"const": "asset_selection", "type": "string"}, {"type": "string"}]},
        },
    }
    data, ui = split_form_schema(raw)
    kind = data["properties"]["kind"]
    # The bare-string escape hatch is filtered, leaving a single const variant,
    # which collapses to a top-level const + type.
    assert "anyOf" not in kind
    assert kind["const"] == "asset_selection"
    assert kind["type"] == "string"
    # The forced field is hidden in the uiSchema.
    assert ui["kind"] == {"ui:widget": "hidden"}


def test_follows_refs_to_harvest_ui_hints_without_inlining():
    raw = {
        "type": "object",
        "properties": {
            "nested": {"$ref": "#/$defs/Nested", "ui:placeholder": "from prop"},
        },
        "$defs": {
            "Nested": {
                "type": "object",
                "ui:widget": "hidden",
                "properties": {"x": {"type": "string"}},
            },
        },
    }
    data, ui = split_form_schema(raw)
    # The data schema preserves the $ref for RJSF to resolve itself.
    assert data["properties"]["nested"]["$ref"] == "#/$defs/Nested"
    # ui:* hints from both the property node and the referenced node are lifted.
    assert ui["nested"]["ui:placeholder"] == "from prop"
    assert ui["nested"]["ui:widget"] == "hidden"


def test_recurses_items_and_additional_properties():
    raw = {
        "type": "object",
        "properties": {
            "tags": {"type": "array", "items": {"type": "string", "ui:widget": "textarea"}},
            "extra": {"type": "object", "additionalProperties": {"ui:placeholder": "value"}},
        },
    }
    _, ui = split_form_schema(raw)
    assert ui["tags"]["items"] == {"ui:widget": "textarea"}
    assert ui["extra"]["additionalProperties"] == {"ui:placeholder": "value"}


def test_end_to_end_real_model_schema():
    """Drive a real Resolvable through model_json_schema() then split it."""

    @dataclass
    class MyComponent(dg.Resolvable):
        required_value: str
        optional_value: Annotated[
            str | None,
            Resolver.default(form_config=ComponentFormConfig(placeholder="optional")),
        ] = None

        @classmethod
        def get_form_config(cls):
            return ComponentFormConfig(label="My Component", editable=True)

    raw = MyComponent.model().model_json_schema()
    data, ui = split_form_schema(raw)

    # Component-level form config surfaces as standard JSON Schema keys, retained
    # on the data schema.
    assert data.get("title") == "My Component"
    assert data.get(APP_MANAGED) is True

    # The injectable ``| str`` variant is gone where a richer variant exists; the
    # placeholder hint is lifted into the uiSchema.
    assert ui["optional_value"]["ui:placeholder"] == "optional"

    # No Dagster sentinels leak into the data schema.
    assert UNSET_DEFAULT_SENTINEL not in repr(data)

    # No inline ui:* keys remain anywhere in the data schema.
    assert "ui:" not in repr(data)
