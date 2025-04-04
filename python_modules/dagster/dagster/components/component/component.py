import inspect
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel
from typing_extensions import Self

from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component_scaffolder import DefaultComponentScaffolder
from dagster.components.resolved.base import Resolvable
from dagster.components.scaffold.scaffold import scaffold_with

if TYPE_CHECKING:
    from dagster.components.core.context import ComponentLoadContext


class ComponentMetadata(BaseModel):
    """Metadata assigned to the Component."""

    author: Optional[str] = None
    tags: Optional[Sequence[str]] = None


@scaffold_with(DefaultComponentScaffolder)
class Component(ABC):
    @classmethod
    def __dg_package_entry__(cls) -> None: ...

    @classmethod
    def get_schema(cls) -> Optional[type[BaseModel]]:
        return None

    @classmethod
    def get_metadata(cls) -> ComponentMetadata:
        return ComponentMetadata()

    @classmethod
    def get_model_cls(cls) -> Optional[type[BaseModel]]:
        if issubclass(cls, Resolvable):
            return cls.model()

        # handle existing overrides for backwards compatibility
        cls_from_get_schema = cls.get_schema()
        if cls_from_get_schema:
            return cls_from_get_schema

        return None

    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return {}

    @abstractmethod
    def build_defs(self, context: "ComponentLoadContext") -> Definitions: ...

    @classmethod
    def load(cls, attributes: Optional[BaseModel], context: "ComponentLoadContext") -> Self:
        if issubclass(cls, Resolvable):
            return (
                cls.resolve_from_model(
                    context.resolution_context.at_path("attributes"),
                    attributes,
                )
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
