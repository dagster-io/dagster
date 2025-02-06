import re
from abc import ABC
from dataclasses import dataclass
from pathlib import Path

COMPONENT_TYPE_REGEX = re.compile(r"^([a-zA-Z0-9_]+)@([a-zA-Z0-9_\.]+)$")


def _name_and_namespace_from_type(typename: str) -> tuple[str, str]:
    match = COMPONENT_TYPE_REGEX.match(typename)
    if not match:
        raise ValueError(f"Invalid component type name: {typename}")
    return match.group(1), match.group(2)


@dataclass(frozen=True)
class ComponentKey(ABC):
    name: str
    namespace: str

    def to_typename(self) -> str:
        return f"{self.name}@{self.namespace}"

    @staticmethod
    def from_typename(typename: str, dirpath: Path) -> "ComponentKey":
        if typename.endswith(".py"):
            return LocalComponentKey.from_type(typename, dirpath)
        else:
            return GlobalComponentKey.from_typename(typename)


@dataclass(frozen=True)
class GlobalComponentKey(ComponentKey):
    @staticmethod
    def from_typename(typename: str) -> "GlobalComponentKey":
        name, namespace = _name_and_namespace_from_type(typename)
        return GlobalComponentKey(name=name, namespace=namespace)


@dataclass(frozen=True)
class LocalComponentKey(ComponentKey):
    dirpath: Path

    @staticmethod
    def from_type(typename: str, dirpath: Path) -> "LocalComponentKey":
        name, namespace = _name_and_namespace_from_type(typename)
        return LocalComponentKey(name=name, namespace=namespace, dirpath=dirpath)

    @property
    def python_file(self) -> Path:
        return self.dirpath / self.namespace
