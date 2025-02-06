from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar, get_args

from dagster._core.errors import DagsterInvariantViolationError
from pydantic import BaseModel
from typing_extensions import Self

if TYPE_CHECKING:
    from dagster_components.core.schema.resolver import ResolutionContext

T_Model = TypeVar("T_Model", bound=BaseModel)
T_Resolved = TypeVar("T_Resolved")
T = TypeVar("T")

FieldResolver = Callable[["ResolutionContext", T_Model], Any]

RESOLVE_METHOD_PREFIX = "resolve_"


class Resolver(Generic[T_Model, T_Resolved]):
    __ignored_fields__ = set()

    @property
    def resolved_type(self) -> type[T_Resolved]:
        generic_base = getattr(self.__class__, "__orig_bases__")[0]
        return get_args(generic_base)[1]

    def _get_default_resolver(self, model: T_Model, field_name: str) -> FieldResolver:
        return lambda context, model: context.resolve_value(getattr(model, field_name))

    def _get_field_resolvers(self, model: T_Model) -> Mapping[str, FieldResolver]:
        field_resolvers = {
            k: self._get_default_resolver(model, k)
            for k in model.model_fields.keys()
            if k not in self.__ignored_fields__
        }
        for attr in dir(self):
            if attr == "resolve_as":
                continue
            if attr.startswith(RESOLVE_METHOD_PREFIX):
                field_name = attr.split(RESOLVE_METHOD_PREFIX)[1]
                field_resolvers[field_name] = getattr(self, attr)
        return field_resolvers

    def get_resolved_properties(
        self, context: "ResolutionContext", model: T_Model
    ) -> Mapping[str, Any]:
        return {
            field_name: field_resolver(context, model)
            for field_name, field_resolver in self._get_field_resolvers(model).items()
        }

    def resolve_as(self, as_type: type[T], context: "ResolutionContext", model: T_Model) -> T:
        return as_type(**self.get_resolved_properties(context, model))

    def resolve(self, context: "ResolutionContext", model: T_Model) -> T_Resolved:
        return self.resolve_as(self.resolved_type, context, model)


class DefaultResolver(Resolver[Any, T_Resolved], Generic[T_Resolved]):
    def __init__(self, resolved_type: type[T_Resolved]):
        self._resolved_type = resolved_type

    @property
    def resolved_type(self) -> type[T_Resolved]:
        return self._resolved_type


class ResolvableModel(BaseModel, Generic[T_Resolved]):
    @property
    def _resolved_type(self) -> type[T_Resolved]:
        resolvable_model_base_class = next(
            base for base in self.__class__.__bases__ if issubclass(base, ResolvableModel)
        )
        generic_args = resolvable_model_base_class.__pydantic_generic_metadata__["args"]
        if len(generic_args) != 1:
            raise DagsterInvariantViolationError(
                "Subclasses of `ResolvableModel` must have exactly one generic type argument. "
                "Make sure to specify subclasses as `class MyModel(ResolvableModel[<type>])` or "
                "override `get_resolver()` in the subclass."
            )
        return generic_args[0]

    def get_resolver(self) -> Resolver[Self, T_Resolved]:
        return DefaultResolver[T_Resolved](self._resolved_type)

    def resolve(self, context: "ResolutionContext") -> T_Resolved:
        return self.get_resolver().resolve(context, self)

    def resolve_as(self, as_type: type[T_Resolved], context: "ResolutionContext") -> T_Resolved:
        print(self.get_resolver())
        return self.get_resolver().resolve_as(as_type, context, self)
