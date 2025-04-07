import textwrap
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Literal, Optional, overload

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
class PackageEntryKey:
    namespace: str
    name: str

    @property
    def package(self) -> str:
        return self.namespace.split(".")[0]

    def to_typename(self) -> str:
        return f"{self.namespace}.{self.name}"

    @staticmethod
    def from_typename(typename: str) -> "PackageEntryKey":
        parts = typename.split(".")
        for part in parts:
            if not part.isidentifier():
                raise ValueError(_generate_invalid_component_typename_error_message(typename))
        if len(parts) < 2:
            raise ValueError(_generate_invalid_component_typename_error_message(typename))
        namespace, _, name = typename.rpartition(".")
        return PackageEntryKey(name=name, namespace=namespace)


###########
# TYPE DATA
###########
PackageEntryType: TypeAlias = Literal["component", "scaffold-target"]


class LibraryEntryTypeData(ABC):
    @property
    @abstractmethod
    def entry_type(self) -> PackageEntryType:
        pass


@whitelist_for_serdes
@record
class ComponentTypeData(LibraryEntryTypeData):
    schema: Optional[dict[str, Any]]

    @property
    def entry_type(self) -> PackageEntryType:
        return "component"


@whitelist_for_serdes
@record
class ScaffoldTargetTypeData(LibraryEntryTypeData):
    schema: Optional[dict[str, Any]]

    @property
    def entry_type(self) -> PackageEntryType:
        return "scaffold-target"


###############
# PACKAGE ENTRY
###############
@whitelist_for_serdes
@record
class PackageEntrySnap:
    key: PackageEntryKey
    summary: Optional[str]
    description: Optional[str]
    type_data: Sequence[LibraryEntryTypeData]

    @property
    def types(self) -> Sequence[PackageEntryType]:
        return [type_data.entry_type for type_data in self.type_data]

    @overload
    def get_type_data(self, entry_type: Literal["component"]) -> Optional[ComponentTypeData]: ...

    @overload
    def get_type_data(
        self, entry_type: Literal["scaffold-target"]
    ) -> Optional[ScaffoldTargetTypeData]: ...

    def get_type_data(self, entry_type: PackageEntryType) -> Optional[LibraryEntryTypeData]:
        for type_data in self.type_data:
            if type_data.entry_type == entry_type:
                return type_data
        return None

    @property
    def scaffolder_schema(self) -> Optional[dict[str, Any]]:
        scaffolder_data = self.get_type_data("scaffold-target")
        return scaffolder_data.schema if scaffolder_data else None

    @property
    def component_schema(self) -> Optional[dict[str, Any]]:
        component_data = self.get_type_data("component")
        return component_data.schema if component_data else None
