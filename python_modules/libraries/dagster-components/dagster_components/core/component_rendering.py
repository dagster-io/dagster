import functools
import os
import typing
from typing import (
    Annotated,
    Any,
    Callable,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    get_origin,
)

import dagster._check as check
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._record import record
from jinja2.nativetypes import NativeTemplate
from pydantic import BaseModel, ConfigDict, TypeAdapter

T = TypeVar("T")

REF_BASE = "#/$defs/"
REF_TEMPLATE = f"{REF_BASE}{{model}}"

JSON_SCHEMA_EXTRA_KEY = "requires_rendering_scope"


def automation_condition_scope() -> Mapping[str, Any]:
    return {
        "eager": AutomationCondition.eager,
        "on_cron": AutomationCondition.on_cron,
    }


def requires_additional_scope(subschema: Mapping[str, Any]) -> bool:
    raw = check.opt_inst(subschema.get(JSON_SCHEMA_EXTRA_KEY), bool)
    return raw or False


def _env(key: str) -> Optional[str]:
    return os.environ.get(key)


ShouldRenderFn = Callable[[Sequence[Union[str, int]]], bool]


@record(checked=False)
class RenderingMetadata:
    """Stores metadata about how a field should be rendered.

    Examples:
    ```python
    class MyModel(BaseModel):
        some_field: Annotated[str, RenderingMetadata(output_type=MyOtherModel)]
        opt_field: Annotated[Optional[str], RenderingMetadata(output_type=(None, MyOtherModel))]
    ```
    """

    output_type: Type


def _get_expected_type(annotation: Type) -> Optional[Type]:
    origin = get_origin(annotation)
    if origin is Annotated:
        _, f_metadata, *_ = typing.get_args(annotation)
        if isinstance(f_metadata, RenderingMetadata):
            return f_metadata.output_type
    else:
        return annotation
    return None


class RenderedModel(BaseModel):
    """Base class for models that get rendered lazily."""

    model_config = ConfigDict(json_schema_extra={JSON_SCHEMA_EXTRA_KEY: True})

    def render_properties(self, value_resolver: "TemplatedValueResolver") -> Mapping[str, Any]:
        """Returns a dictionary of rendered properties for this class."""
        rendered_properties = value_resolver.render_obj(self.model_dump(exclude_unset=True))

        # validate that the rendered properties match the output type
        for k, v in rendered_properties.items():
            annotation = self.__annotations__[k]
            # TODO this was my first attempt to handle inheritance
            # annotation = self.model_fields[k].annotation
            # if annotation is None:
            #     raise Exception(f"Annotation missing for field {k}")
            expected_type = _get_expected_type(annotation)
            if expected_type is not None:
                # hook into pydantic's type validation to handle complicated stuff like Optional[Mapping[str, int]]
                TypeAdapter(
                    expected_type, config={"arbitrary_types_allowed": True}
                ).validate_python(v)

        return rendered_properties


@record
class TemplatedValueResolver:
    context: Mapping[str, Any]

    @staticmethod
    def default() -> "TemplatedValueResolver":
        return TemplatedValueResolver(
            context={"env": _env, "automation_condition": automation_condition_scope()}
        )

    def with_context(self, **additional_context) -> "TemplatedValueResolver":
        return TemplatedValueResolver(context={**self.context, **additional_context})

    def _render_value(self, val: Any) -> Any:
        """Renders a single value, if it is a templated string."""
        return NativeTemplate(val).render(**self.context) if isinstance(val, str) else val

    def _render_obj(
        self,
        obj: Any,
        valpath: Optional[Sequence[Union[str, int]]],
        should_render: Callable[[Sequence[Union[str, int]]], bool],
    ) -> Any:
        """Recursively renders templated values in a nested object, based on the provided should_render function."""
        if valpath is not None and not should_render(valpath):
            return obj
        elif isinstance(obj, dict):
            # render all values in the dict
            return {
                k: self._render_obj(
                    v, [*valpath, k] if valpath is not None else None, should_render
                )
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            # render all values in the list
            return [
                self._render_obj(v, [*valpath, i] if valpath is not None else None, should_render)
                for i, v in enumerate(obj)
            ]
        else:
            return self._render_value(obj)

    def render_obj(self, val: Any) -> Any:
        """Recursively renders templated values in a nested object."""
        return self._render_obj(val, None, lambda _: True)

    def render_params(self, val: T, target_type: Type) -> T:
        """Given a raw params value, preprocesses it by rendering any templated values that are not marked as deferred in the target_type's json schema."""
        json_schema = (
            target_type.model_json_schema() if issubclass(target_type, BaseModel) else None
        )
        if json_schema is None:
            should_render = lambda _: True
        else:
            should_render = functools.partial(
                can_render_with_default_scope, json_schema=json_schema, subschema=json_schema
            )
        return self._render_obj(val, [], should_render=should_render)


def can_render_with_default_scope(
    valpath: Sequence[Union[str, int]], json_schema: Mapping[str, Any], subschema: Mapping[str, Any]
) -> bool:
    """Given a valpath and the json schema of a given target type, determines if there is a rendering scope
    required to render the value at the given path.
    """
    # List[ComplexType] (e.g.) will contain a reference to the complex type schema in the
    # top-level $defs, so we dereference it here.
    if "$ref" in subschema:
        subschema = json_schema["$defs"].get(subschema["$ref"][len(REF_BASE) :])

    if requires_additional_scope(subschema):
        return False
    elif len(valpath) == 0:
        return True

    # Optional[ComplexType] (e.g.) will contain multiple schemas in the "anyOf" field
    if "anyOf" in subschema:
        return all(
            can_render_with_default_scope(valpath, json_schema, inner)
            for inner in subschema["anyOf"]
        )

    el = valpath[0]
    if isinstance(el, str):
        # valpath: ['field']
        # field: X
        inner = subschema.get("properties", {}).get(el)
    elif isinstance(el, int):
        # valpath: ['field', 0]
        # field: List[X]
        inner = subschema.get("items")
    else:
        check.failed(f"Unexpected valpath element: {el}")

    # the path wasn't valid, or unspecified
    if not inner:
        return subschema.get("additionalProperties", True)

    _, *rest = valpath
    return can_render_with_default_scope(rest, json_schema, inner)
