from collections.abc import Mapping, Set
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar, get_args

from dagster._core.errors import DagsterInvalidDefinitionError
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from dagster_components.core.schema.context import ResolutionContext

FIELD_RESOLVER_PREFIX = "resolve_"

T = TypeVar("T")


class ResolvableSchema(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")

    @property
    def _resolved_type(self) -> type:
        generic_args = get_args(self.__class__.__pydantic_generic_metadata__)
        if len(generic_args) == 0:
            # if no generic type is specified, resolve back to the base type
            return self.__class__
        elif len(generic_args) > 1:
            raise DagsterInvalidDefinitionError(
                f"Expected at most one generic argument for type: `{self.__class__}`"
            )
        resolved_type = generic_args[0]
        if isinstance(resolved_type, str):
            raise DagsterInvalidDefinitionError(
                f"Attempted to directly resolve a `ResolvableSchema` ({self.__class__}) with a ForwardRef: `{resolved_type}`. "
                "Use `resolve_as` instead."
            )
        return resolved_type

    def _resolve_field(self, context: "ResolutionContext", field: str) -> Any:
        return context.resolve_value(getattr(self, field))

    def resolve_fields(
        self, context: "ResolutionContext", exclude: Optional[Set[str]] = None
    ) -> Mapping[str, Any]:
        """Returns a mapping of field names to resolved values for those fields."""
        return {
            field: context.resolve_value(getattr(self, field))
            for field in self.model_fields
            if exclude is None or field not in exclude
        }

    def resolve_as(self, as_type: type[T], context: "ResolutionContext") -> T:
        return as_type(**self.resolve_fields(context))

    def resolve(self, context: "ResolutionContext") -> T:
        return self.resolve_as(self._resolved_type, context)
