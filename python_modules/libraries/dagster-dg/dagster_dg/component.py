import copy
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional


@dataclass
class RemoteComponentType:
    name: str
    package: str
    summary: Optional[str]
    description: Optional[str]
    generate_params_schema: Optional[Mapping[str, Any]]  # json schema
    component_params_schema: Optional[Mapping[str, Any]]  # json schema

    @property
    def key(self) -> str:
        return self.name


class RemoteComponentRegistry:
    @classmethod
    def from_dict(cls, components: Dict[str, Mapping[str, Any]]) -> "RemoteComponentRegistry":
        return RemoteComponentRegistry(
            {key: RemoteComponentType(**value) for key, value in components.items()}
        )

    def __init__(self, components: Dict[str, RemoteComponentType]):
        self._components: Dict[str, RemoteComponentType] = copy.copy(components)

    @staticmethod
    def empty() -> "RemoteComponentRegistry":
        return RemoteComponentRegistry({})

    def has(self, name: str) -> bool:
        return name in self._components

    def get(self, name: str) -> RemoteComponentType:
        return self._components[name]

    def keys(self) -> Iterable[str]:
        return self._components.keys()

    def __repr__(self) -> str:
        return f"<RemoteComponentRegistry {list(self._components.keys())}>"
