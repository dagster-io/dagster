import inspect
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel
from typing_extensions import Self

from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component_scaffolder import DefaultComponentScaffolder
from dagster.components.resolved.base import Resolvable
from dagster.components.scaffold.scaffold import scaffold_with

if TYPE_CHECKING:
    from dagster.components.core.context import ComponentLoadContext


@dataclass
class ComponentRequirements:
    env: dict[str, set[Path]]

    def __or__(self, other: "ComponentRequirements") -> "ComponentRequirements":
        return ComponentRequirements(
            env={
                key: (self.env.get(key, set()) | other.env.get(key, set()))
                for key in set(self.env.keys()) | set(other.env.keys())
            }
        )

    def to_json(self, components_root_path: Path) -> dict[str, Any]:
        return {
            "env": {
                key: [str(path.relative_to(components_root_path)) for path in paths]
                for key, paths in self.env.items()
            }
        }


@scaffold_with(DefaultComponentScaffolder)
class Component(ABC):
    @classmethod
    def __dg_library_object__(cls) -> None: ...

    @classmethod
    def get_schema(cls) -> Optional[type[BaseModel]]:
        return None

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

    def get_requirements(self, context: "ComponentLoadContext") -> ComponentRequirements:
        return ComponentRequirements(env={})

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
