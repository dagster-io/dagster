from abc import abstractmethod
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel, ConfigDict

from dagster_components.core.schema.metadata import get_resolution_metadata

if TYPE_CHECKING:
    from dagster_components.core.schema.resolver import ResolveContext

T = TypeVar("T")


class ResolvableModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    def _get_resolved_field(self, field_name: str, context: "ResolveContext") -> tuple[str, Any]:
        resolution_metadata = get_resolution_metadata(self.__annotations__[field_name])
        resolved_field_name = resolution_metadata.resolved_field_name or field_name

        field_resolver = getattr(self, f"resolve_{resolved_field_name}", None)
        if field_resolver:
            resolved_field_value = field_resolver(context)
        else:
            resolved_field_value = context.resolve_value(getattr(self, field_name))

        return resolved_field_name, resolved_field_value

    def resolve_properties(self, context: "ResolveContext") -> Mapping[str, Any]:
        return dict(self._get_resolved_field(k, context) for k in self.model_fields.keys())

    def resolve_as(self, as_type: type[T], context: "ResolveContext") -> T:
        return as_type(**self.resolve_properties(context))

    @abstractmethod
    def resolve(self, context: "ResolveContext") -> Any: ...
