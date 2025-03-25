import inspect
from abc import ABC
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Optional

from typing_extensions import Self

from dagster_components.component.component_scaffolder import DefaultComponentScaffolder
from dagster_components.core.defs_loader import DefsLoader
from dagster_components.resolved.model import ResolvableModel, ResolvedFrom, resolve_model
from dagster_components.scaffold.scaffold import scaffold_with

if TYPE_CHECKING:
    from dagster_components.core.context import DefsModuleLoadContext


@scaffold_with(DefaultComponentScaffolder)
class Component(DefsLoader, ABC):
    @classmethod
    def __dg_library_object__(cls) -> None: ...

    @classmethod
    def get_schema(cls) -> Optional[type["ResolvableModel"]]:
        from dagster_components.resolved.model import ResolvedFrom, get_model_type

        if issubclass(cls, ResolvableModel):
            return cls

        if issubclass(cls, ResolvedFrom):
            return get_model_type(cls)
        return None

    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return {}

    @classmethod
    def load(
        cls, attributes: Optional["ResolvableModel"], context: "DefsModuleLoadContext"
    ) -> Self:
        if issubclass(cls, ResolvableModel):
            # If the Component is a DSLSchema, the attributes in this case are an instance of itself
            assert isinstance(attributes, cls)
            return attributes

        elif issubclass(cls, ResolvedFrom):
            return (
                resolve_model(attributes, cls, context.resolution_context.at_path("attributes"))
                if attributes
                else cls()
            )
        else:
            # If the Component does not implement anything from Resolved, try to instantiate it without
            # argument.
            return cls()

    @classmethod
    def get_description(cls) -> Optional[str]:
        return inspect.getdoc(cls)
