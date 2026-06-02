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
        if isinstance(variants, list):
            filtered = variants if key == "allOf" else _filter_jinja_string_variants(variants)
            out[key] = [_transform(v, root, {}, visiting) for v in filtered]

    # Pydantic emits discriminator fields like ``Literal["asset_selection"]`` as
    # ``anyOf: [{const: "...", type: "string"}, {type: "string"}]`` (the second
    # variant is the Jinja escape hatch filtered out above). Collapse a
    # remaining single-variant ``anyOf``/``oneOf`` whose only entry is a
    # ``const`` back to a top-level ``const`` so downstream code recognises it.
    for key in ("anyOf", "oneOf"):
        variants = out.get(key)
        if (
            isinstance(variants, list)
            and len(variants) == 1
            and isinstance(variants[0], Mapping)
            and "const" in variants[0]
        ):
            only = variants[0]
            if "const" not in out:
                out["const"] = only["const"]
            only_type = only.get("type")
            if "type" not in out and isinstance(only_type, str):
                out["type"] = only_type
            del out[key]

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
