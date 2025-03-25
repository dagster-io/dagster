import textwrap
from typing import Any, Optional

from dagster_shared.record import record
from dagster_shared.serdes.serdes import whitelist_for_serdes


def _generate_invalid_component_typename_error_message(typename: str) -> str:
    return textwrap.dedent(f"""
        Invalid component type name: `{typename}`.
        Type names must be a "."-separated string of valid Python identifiers with at least two segments.
    """)


@whitelist_for_serdes
@record(kw_only=False)
class LibraryObjectKey:
    namespace: str
    name: str

    def to_typename(self) -> str:
        return f"{self.namespace}.{self.name}"

    @staticmethod
    def from_typename(typename: str) -> "LibraryObjectKey":
        parts = typename.split(".")
        for part in parts:
            if not part.isidentifier():
                raise ValueError(_generate_invalid_component_typename_error_message(typename))
        if len(parts) < 2:
            raise ValueError(_generate_invalid_component_typename_error_message(typename))
        namespace, _, name = typename.rpartition(".")
        return LibraryObjectKey(name=name, namespace=namespace)


@whitelist_for_serdes
@record
class ScaffolderSnap:
    schema: Optional[dict[str, Any]]


@whitelist_for_serdes
@record
class LibraryObjectSnap:
    key: LibraryObjectKey
    summary: Optional[str]
    description: Optional[str]
    scaffolder: Optional["ScaffolderSnap"]

    @property
    def scaffolder_schema(self) -> Optional[dict[str, Any]]:
        return self.scaffolder.schema if self.scaffolder else None


@whitelist_for_serdes
@record
class ComponentTypeSnap(LibraryObjectSnap):
    schema: Optional[dict[str, Any]]
