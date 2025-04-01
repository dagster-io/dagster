import textwrap
from typing import Any, Literal, Optional

from typing_extensions import TypeAlias

from dagster_shared.record import record
from dagster_shared.serdes.serdes import whitelist_for_serdes


def _generate_invalid_component_typename_error_message(typename: str) -> str:
    return textwrap.dedent(f"""
        Invalid component type name: `{typename}`.
        Type names must be a "."-separated string of valid Python identifiers with at least two segments.
    """)


@whitelist_for_serdes
@record(kw_only=False)
class LibraryEntryKey:
    namespace: str
    name: str

    def to_typename(self) -> str:
        return f"{self.namespace}.{self.name}"

    @staticmethod
    def from_typename(typename: str) -> "LibraryEntryKey":
        parts = typename.split(".")
        for part in parts:
            if not part.isidentifier():
                raise ValueError(_generate_invalid_component_typename_error_message(typename))
        if len(parts) < 2:
            raise ValueError(_generate_invalid_component_typename_error_message(typename))
        namespace, _, name = typename.rpartition(".")
        return LibraryEntryKey(name=name, namespace=namespace)


ScaffolderScope: TypeAlias = Literal["global", "project", "defs"]


@whitelist_for_serdes
@record
class ScaffolderSnap:
    scope: ScaffolderScope
    schema: Optional[dict[str, Any]]


@whitelist_for_serdes
@record
class LibraryEntrySnap:
    key: LibraryEntryKey
    summary: Optional[str]
    description: Optional[str]
    scaffolder: Optional["ScaffolderSnap"]

    @property
    def scaffolder_schema(self) -> Optional[dict[str, Any]]:
        return self.scaffolder.schema if self.scaffolder else None

    @property
    def scaffolder_scope(self) -> Optional[ScaffolderScope]:
        return self.scaffolder.scope if self.scaffolder else None


@whitelist_for_serdes
@record
class ComponentTypeSnap(LibraryEntrySnap):
    schema: Optional[dict[str, Any]]
