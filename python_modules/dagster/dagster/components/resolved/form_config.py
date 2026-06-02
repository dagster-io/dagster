"""Typed JSON Schema metadata for the app-managed components form editor.

The :class:`ComponentFormConfig` record provides a type-safe API for
configuring how a component class — and the individual fields on its model —
are rendered in the Dagster app-managed components editor. Component-level
values serialize to ``x-app-managed`` (a Python-side filter) and the standard
JSON Schema ``title``. Field-level values serialize to react-jsonschema-form's
inline ``ui:*`` keys, which the frontend extracts into a parallel ``uiSchema``.
"""

from typing import Any

from dagster_shared.record import record

# Python-side filter marking a component class as app-managed (i.e. editable
# from the app). Not consumed by the form renderer; checked by
# ``fetch_component_types`` to decide which component types appear in the
# editor's type picker.
APP_MANAGED = "x-app-managed"

# Sentinel emitted as the ``default`` for fields whose real default is not
# JSON-serializable (see ``derive_model_type`` in ``base.py``). The form-schema
# split (:func:`dagster.components.resolved.form_schema.split_form_schema`)
# strips it so react-jsonschema-form sees "no default". Defined here so the
# encode side (``base.py``) and the decode side (``form_schema.py``) share one
# source of truth; ``base.py`` imports it as ``_Unset``.
UNSET_DEFAULT_SENTINEL = "__DAGSTER_UNSET_DEFAULT__"

# Frontend marker: the field whose value drives the auto-generated component
# id. Not an RJSF rendering hint, so it stays under the ``x-app-*`` namespace.
APP_ID_SOURCE = "x-app-id-source"


@record
class ComponentFormConfig:
    """Form metadata for a component class or one of its fields.

    Used at two levels:

    **Component level** — override :meth:`Resolvable.get_form_config`::

        class MyComponent(Component, Model, Resolvable):
            @classmethod
            def get_form_config(cls) -> ComponentFormConfig:
                return ComponentFormConfig(label="My Component", editable=True)

    **Field level** — pass to ``Resolver(form_config=...)``::

        name: Annotated[
            str,
            Resolver.default(form_config=ComponentFormConfig(placeholder="e.g. my_job")),
        ]

    Args:
        label: Human-friendly display name. At the component level this is the
            name shown in the type picker. At the field level it overrides the
            default label derived from the field name.
        editable: Component level only. Whether this component type can be
            created and edited from the app. Defaults to False.
        hidden: Field level only. If True, the field is hidden from the form.
        placeholder: Field level only. Placeholder text for the form input.
        multiline: Field level only. If True, render a textarea instead of a
            single-line input.
        id_source: Field level only. If True, the form uses this field's value
            as the suffix in the auto-generated component id (e.g.
            ``MyComponent[<field value>]``). Only one field per component may
            be marked this way, and it must be a required field.
    """

    label: str | None = None
    editable: bool = False
    hidden: bool | None = None
    placeholder: str | None = None
    multiline: bool | None = None
    id_source: bool | None = None

    def to_component_json_schema_extra(self) -> dict[str, Any]:
        """Serialize component-level fields to JSON schema extension keys."""
        out: dict[str, Any] = {}
        if self.editable:
            out[APP_MANAGED] = True
        if self.label is not None:
            # Standard JSON Schema title; RJSF and union variant labels both
            # read it directly.
            out["title"] = self.label
        return out

    def to_field_json_schema_extra(self) -> dict[str, Any]:
        """Serialize field-level fields to inline react-jsonschema-form keys.

        The frontend walks the schema once and lifts these ``ui:*`` entries
        into a parallel ``uiSchema`` for RJSF; no key renaming is needed.
        """
        out: dict[str, Any] = {}
        if self.label is not None:
            out["title"] = self.label
        if self.hidden:
            out["ui:widget"] = "hidden"
        elif self.multiline:
            out["ui:widget"] = "textarea"
        if self.placeholder is not None:
            out["ui:placeholder"] = self.placeholder
        if self.id_source:
            out[APP_ID_SOURCE] = True
        return out
