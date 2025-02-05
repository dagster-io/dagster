from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from dagster._core.errors import DagsterInvariantViolationError
from pydantic import BaseModel, ConfigDict

from dagster_components.core.schema.metadata import get_resolution_metadata

if TYPE_CHECKING:
    from dagster_components.core.schema.resolver import ResolutionContext

T = TypeVar("T")


class ResolvableModel(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")

    @property
    def _resolved_type(self) -> type[T]:
        resolvable_model_base_class = next(
            base for base in self.__class__.__bases__ if issubclass(base, ResolvableModel)
        )
        generic_args = resolvable_model_base_class.__pydantic_generic_metadata__["args"]
        if len(generic_args) != 1:
            raise DagsterInvariantViolationError(
                "Subclasses of `ResolvableModel` must have exactly one generic type argument. "
                "Make sure to specify subclasses as `class MyModel(ResolvableModel[<type>])` or "
                "override `resolve()` in the subclass."
            )
        return generic_args[0]

    def _get_annotation(self, field_name: str) -> type:
        for base in self.__class__.__mro__:
            if field_name in base.__annotations__:
                return base.__annotations__[field_name]
        raise ValueError(f"Field {field_name} not found in any base class.")

    def _get_resolved_field(self, field_name: str, context: "ResolutionContext") -> tuple[str, Any]:
        resolution_metadata = get_resolution_metadata(self._get_annotation(field_name))
        resolved_field_name = resolution_metadata.resolved_field_name or field_name

        field_resolver = getattr(self, f"resolve_{resolved_field_name}", None)
        if field_resolver:
            resolved_field_value = field_resolver(context)
        else:
            resolved_field_value = context.resolve_value(getattr(self, field_name))

        return resolved_field_name, resolved_field_value

    def get_resolved_properties(self, context: "ResolutionContext") -> Mapping[str, Any]:
        return dict(self._get_resolved_field(k, context) for k in self.model_fields.keys())

    def resolve_as(self, as_type: type[T], context: "ResolutionContext") -> T:
        return as_type(**self.get_resolved_properties(context))

    def resolve(self, context: "ResolutionContext") -> T:
        return self.resolve_as(self._resolved_type, context)
