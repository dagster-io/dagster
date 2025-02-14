import re
import textwrap
from abc import ABC
from dataclasses import dataclass
from pathlib import Path

LOCAL_COMPONENT_IDENTIFIER = "file:"

_COMPONENT_NAME_REGEX = r"[a-zA-Z0-9_]+"
_FILE_PATH_REGEX = r"[a-zA-Z0-9_\.\/-]+"
_LOCAL_NAMESPACE_REGEX = rf"{LOCAL_COMPONENT_IDENTIFIER}{_FILE_PATH_REGEX}"
_GLOBAL_NAMESPACE_REGEX = r"[a-zA-Z0-9_\.]+"

COMPONENT_TYPENAME_REGEX = re.compile(
    rf"^({_COMPONENT_NAME_REGEX})@(({_LOCAL_NAMESPACE_REGEX})|({_GLOBAL_NAMESPACE_REGEX}))$"
)


def _generate_invalid_component_typename_error_message(typename: str) -> str:
    return textwrap.dedent(f"""
        Invalid component type name: `{typename}`.
        Type names must match regex: `{COMPONENT_TYPENAME_REGEX.pattern}`.
    """)


def _name_and_namespace_from_type(typename: str) -> tuple[str, str]:
    match = COMPONENT_TYPENAME_REGEX.match(typename)
    if not match:
        raise ValueError(_generate_invalid_component_typename_error_message(typename))
    return match.group(1), match.group(2)


@dataclass(frozen=True)
class ComponentKey(ABC):
    name: str
    namespace: str

    def to_typename(self) -> str:
        return f"{self.name}@{self.namespace}"

    @staticmethod
    def from_typename(typename: str, dirpath: Path) -> "ComponentKey":
        name, namespace = _name_and_namespace_from_type(typename)
        if namespace.startswith(LOCAL_COMPONENT_IDENTIFIER):
            return LocalComponentKey(name, namespace, dirpath)
        else:
            return GlobalComponentKey(name, namespace)


@dataclass(frozen=True)
class GlobalComponentKey(ComponentKey):
    @staticmethod
    def from_typename(typename: str) -> "GlobalComponentKey":
        name, namespace = _name_and_namespace_from_type(typename)
        return GlobalComponentKey(name=name, namespace=namespace)


@dataclass(frozen=True)
class LocalComponentKey(ComponentKey):
    dirpath: Path

    def __post_init__(self) -> None:
        if not self.python_file.resolve().is_relative_to(self.dirpath.resolve()):
            raise ValueError(f"File {self.namespace} must be within directory: {self.dirpath}")

    @staticmethod
    def from_typename(typename: str, dirpath: Path) -> "LocalComponentKey":
        name, namespace = _name_and_namespace_from_type(typename)
        return LocalComponentKey(name=name, namespace=namespace, dirpath=dirpath)

    @property
    def python_file(self) -> Path:
        relative_path = self.namespace[len(LOCAL_COMPONENT_IDENTIFIER) :]
        return self.dirpath / relative_path
