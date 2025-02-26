import textwrap
from dataclasses import dataclass


def _generate_invalid_component_typename_error_message(typename: str) -> str:
    return textwrap.dedent(f"""
        Invalid component type name: `{typename}`.
        Type names must be a "."-separated string of valid Python identifiers with at least two segments.
    """)


@dataclass(frozen=True)
class ComponentKey:
    namespace: str
    name: str

    def to_typename(self) -> str:
        return f"{self.namespace}.{self.name}"

    @staticmethod
    def from_typename(typename: str) -> "ComponentKey":
        parts = typename.split(".")
        for part in parts:
            if not part.isidentifier():
                raise ValueError(_generate_invalid_component_typename_error_message(typename))
        if len(parts) < 2:
            raise ValueError(_generate_invalid_component_typename_error_message(typename))
        namespace, _, name = typename.rpartition(".")
        return ComponentKey(name=name, namespace=namespace)
