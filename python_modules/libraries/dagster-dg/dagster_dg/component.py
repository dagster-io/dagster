import copy
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from dagster_dg.utils import is_valid_json

if TYPE_CHECKING:
    from dagster_dg.context import DgContext


@dataclass
class RemoteComponentType:
    name: str
    package: str
    summary: Optional[str]
    description: Optional[str]
    scaffold_params_schema: Optional[Mapping[str, Any]]  # json schema
    component_params_schema: Optional[Mapping[str, Any]]  # json schema

    @property
    def key(self) -> str:
        return self.name


class RemoteComponentRegistry:
    @classmethod
    def from_dg_context(cls, dg_context: "DgContext") -> "RemoteComponentRegistry":
        if dg_context.config.use_dg_managed_environment:
            dg_context.ensure_uv_lock()

        if dg_context.has_cache:
            cache_key = dg_context.get_cache_key("component_registry_data")
            raw_registry_data = dg_context.cache.get(cache_key)
        else:
            cache_key = None
            raw_registry_data = None

        if not raw_registry_data:
            raw_registry_data = dg_context.external_components_command(["list", "component-types"])
            if dg_context.has_cache and cache_key and is_valid_json(raw_registry_data):
                dg_context.cache.set(cache_key, raw_registry_data)

        registry_data = json.loads(raw_registry_data)
        return cls.from_dict(registry_data)

    @classmethod
    def from_dict(cls, components: dict[str, Mapping[str, Any]]) -> "RemoteComponentRegistry":
        return RemoteComponentRegistry(
            {key: RemoteComponentType(**value) for key, value in components.items()}
        )

    def __init__(self, components: dict[str, RemoteComponentType]):
        self._components: dict[str, RemoteComponentType] = copy.copy(components)

    @staticmethod
    def empty() -> "RemoteComponentRegistry":
        return RemoteComponentRegistry({})

    def has(self, name: str) -> bool:
        return name in self._components

    def get(self, name: str) -> RemoteComponentType:
        return self._components[name]

    def keys(self) -> Iterable[str]:
        return self._components.keys()

    def items(self) -> Iterable[tuple[str, RemoteComponentType]]:
        for key in sorted(self.keys()):
            yield key, self.get(key)

    def __repr__(self) -> str:
        return f"<RemoteComponentRegistry {list(self._components.keys())}>"
