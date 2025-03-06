import textwrap
from dataclasses import dataclass

from typing_extensions import Self


def _generate_invalid_component_typename_error_message(typename: str) -> str:
    return textwrap.dedent(f"""
        Invalid type name: `{typename}`.
        Type names must be a "."-separated string of valid Python identifiers with at least two segments.
    """)


@dataclass(frozen=True)
class ObjectKey:
    namespace: str
    name: str

    def to_typename(self) -> str:
        return f"{self.namespace}.{self.name}"

    @classmethod
    def from_typename(cls, typename: str) -> Self:
        parts = typename.split(".")
        for part in parts:
            if not part.isidentifier():
                raise ValueError(_generate_invalid_component_typename_error_message(typename))
        if len(parts) < 2:
            raise ValueError(_generate_invalid_component_typename_error_message(typename))
        namespace, _, name = typename.rpartition(".")
        return cls(name=name, namespace=namespace)


@dataclass(frozen=True)
class ComponentKey(ObjectKey): ...
