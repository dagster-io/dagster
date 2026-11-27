"""Split a Dagster-emitted JSON Schema into the (dataSchema, uiSchema) pair that
react-jsonschema-form (RJSF) expects.

The schema produced by ``model_json_schema()`` on a derived component model
carries three Dagster-specific conventions, each emitted elsewhere in the
resolved framework:

- inline ``ui:*`` hint keys + ``title`` — :mod:`dagster.components.resolved.form_config`
- ``default: "__DAGSTER_UNSET_DEFAULT__"`` sentinels for non-serializable
  defaults — ``base.py`` (:data:`UNSET_DEFAULT_SENTINEL`)
- ``anyOf: [..., {"type": "string"}]`` Jinja escape-hatch variants, from the
  ``field_type | str`` "make all fields injectable" step in ``base.py``

This module is the decode side of those conventions. Keeping it next to the
encode side (rather than reimplemented in TypeScript) means the two halves move
together: the GraphQL layer calls :func:`split_form_schema` server-side and
hands the frontend a schema pair it can feed straight to RJSF.
"""

from collections.abc import Mapping
from typing import Any

from dagster.components.resolved.form_config import UNSET_DEFAULT_SENTINEL

# Keys whose values are sub-schema lists that we recurse into.
_VARIANT_KEYS = ("anyOf", "oneOf", "allOf")


def split_form_schema(raw_schema: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    """Split a raw component JSON Schema into ``(data_schema, ui_schema)``.

    ``data_schema`` is the cleaned schema RJSF validates/renders against
    (``ui:*`` keys removed, unset-default sentinels dropped, Jinja string
    escape-hatch variants filtered out). ``ui_schema`` is the parallel RJSF
    uiSchema holding the lifted ``ui:*`` hints.

    ``$ref``s are followed only to harvest ``ui:*`` hints from the referenced
    node; the returned data schema keeps the original ``$ref`` structure so
    RJSF can resolve refs itself. Returns ``({}, {})`` for non-object input.
    """
    if not isinstance(raw_schema, Mapping):
        return {}, {}
    ui_schema: dict[str, Any] = {}
    data_schema = _transform(raw_schema, raw_schema, ui_schema, set())
    return data_schema, ui_schema


def _transform(
    node: Any,
    root: Mapping[str, Any],
    ui_node: dict[str, Any],
    visiting: set[str],
) -> Any:
    if not isinstance(node, Mapping):
        return node

    out: dict[str, Any] = {}
    for k, v in node.items():
        if isinstance(k, str) and k.startswith("ui:"):
            ui_node[k] = v
            continue
        if k == "default" and v == UNSET_DEFAULT_SENTINEL:
            continue
        out[k] = v

    ref = out.get("$ref")
    if isinstance(ref, str) and ref not in visiting:
        # Follow the ref purely to harvest ``ui:*`` hints from the target so the
        # uiSchema mirrors the *resolved* structure RJSF will render. The data
        # schema keeps the ref for RJSF to resolve.
        visiting.add(ref)
        try:
            target = _resolve_ref(ref, root)
            if target is not None:
                _transform(target, root, ui_node, visiting)
        finally:
            visiting.discard(ref)

    for key in _VARIANT_KEYS:
        variants = out.get(key)
        if not isinstance(variants, list):
            continue
        if key == "allOf":
            out[key] = [_transform(v, root, {}, visiting) for v in variants]
            continue
        filtered = _drop_null_variants(variants)
        if len(filtered) < len(variants) and "default" in out and out["default"] is None:
            # The null variant only encodes optionality (``X | None``). With it
            # gone, a null default would seed ``null`` into the form data for a
            # non-null field; omitting the key resolves to the same python-side
            # default.
            del out["default"]
        filtered = _filter_jinja_string_variants(filtered)
        if len(filtered) == 1 and isinstance(filtered[0], Mapping):
            # A single real variant left (e.g. the payload of an ``X | None``
            # optional, an enum ``Literal``, or a tagged-union discriminator
            # ``const``): merge it into the parent so the form renders a plain
            # field instead of a one-option variant picker with a duplicated
            # label. Parent keys (title, description, default) win. UI hints
            # inside the variant lift to this field's ui_node.
            merged = _transform(filtered[0], root, ui_node, visiting)
            del out[key]
            for merged_key, merged_value in merged.items():
                out.setdefault(merged_key, merged_value)
        else:
            out[key] = [_transform(v, root, {}, visiting) for v in filtered]

    properties = out.get("properties")
    if isinstance(properties, Mapping):
        props_out: dict[str, Any] = {}
        for name, sub in properties.items():
            child_ui: dict[str, Any] = {}
            transformed = _transform(sub, root, child_ui, visiting)
            props_out[name] = transformed
            # Discriminator fields collapse to a ``const``; hide them since the
            # value is forced and the user has no meaningful choice to make.
            if isinstance(transformed, Mapping) and "const" in transformed:
                child_ui["ui:widget"] = "hidden"
            if child_ui:
                ui_node[name] = child_ui
        out["properties"] = props_out

    items = out.get("items")
    if isinstance(items, (Mapping, list)):
        child_ui = {}
        out["items"] = _transform(items, root, child_ui, visiting)
        if child_ui:
            ui_node["items"] = child_ui

    additional = out.get("additionalProperties")
    if isinstance(additional, Mapping):
        child_ui = {}
        out["additionalProperties"] = _transform(additional, root, child_ui, visiting)
        if child_ui:
            ui_node["additionalProperties"] = child_ui

    defs = out.get("$defs")
    if isinstance(defs, Mapping):
        out["$defs"] = {name: _transform(sub, root, {}, visiting) for name, sub in defs.items()}

    return out


def _resolve_ref(ref: str, root: Mapping[str, Any]) -> Any:
    if not ref.startswith("#/"):
        return None
    current: Any = root
    for segment in ref[2:].split("/"):
        if not isinstance(current, Mapping):
            return None
        current = current.get(segment)
    return current


def _drop_null_variants(variants: list[Any]) -> list[Any]:
    """Drop ``{"type": "null"}`` variants when any real variant exists.

    The null variant comes from ``X | None`` annotations. Optionality is
    already expressed by the field's absence from ``required``; in the form,
    "leave it empty" is the way to express null, so a null branch in a variant
    picker is never a meaningful choice.
    """
    non_null = [v for v in variants if not (isinstance(v, Mapping) and v.get("type") == "null")]
    return non_null if non_null else variants


def _filter_jinja_string_variants(variants: list[Any]) -> list[Any]:
    """Drop the bare ``{"type": "string"}`` Jinja escape-hatch variant.

    Every resolved field is made injectable via ``field_type | str``, which adds
    a plain string variant alongside the real one. When a richer variant exists
    we hide the bare string so the form renders the real control; if the field
    is genuinely just a string we leave it untouched.
    """
    has_richer_variant = any(
        isinstance(v, Mapping)
        and (v.get("type") != "string" or bool(v.get("enum")) or "const" in v or "properties" in v)
        for v in variants
    )
    if not has_richer_variant:
        return variants
    return [
        v
        for v in variants
        if not (
            isinstance(v, Mapping)
            and v.get("type") == "string"
            and not v.get("enum")
            and "const" not in v
            and "properties" not in v
        )
    ]
