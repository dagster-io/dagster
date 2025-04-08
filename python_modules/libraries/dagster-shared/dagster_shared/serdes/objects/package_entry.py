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
class PluginObjectKey:
    namespace: str
    name: str

    @property
    def package(self) -> str:
        return self.namespace.split(".")[0]

    def to_typename(self) -> str:
        return f"{self.namespace}.{self.name}"

    @staticmethod
    def from_typename(typename: str) -> "PluginObjectKey":
        parts = typename.split(".")
        for part in parts:
            if not part.isidentifier():
                raise ValueError(_generate_invalid_component_typename_error_message(typename))
        if len(parts) < 2:
            raise ValueError(_generate_invalid_component_typename_error_message(typename))
        namespace, _, name = typename.rpartition(".")
        return PluginObjectKey(name=name, namespace=namespace)


###########
# TYPE DATA
###########
PluginObjectFeature: TypeAlias = Literal["component", "scaffold-target"]


class PluginObjectFeatureData(ABC):
    @property
    @abstractmethod
    def feature(self) -> PluginObjectFeature:
        pass


@whitelist_for_serdes
@record
class ComponentFeatureData(PluginObjectFeatureData):
    schema: Optional[dict[str, Any]]

    @property
    def feature(self) -> PluginObjectFeature:
        return "component"


@whitelist_for_serdes
@record
class ScaffoldTargetTypeData(PluginObjectFeatureData):
    schema: Optional[dict[str, Any]]

    @property
    def feature(self) -> PluginObjectFeature:
        return "scaffold-target"


###############
# PACKAGE ENTRY
###############
@whitelist_for_serdes
@record
class PluginObjectSnap:
    key: PluginObjectKey
    summary: Optional[str]
    description: Optional[str]
    owners: Optional[Sequence[str]]
    tags: Optional[Sequence[str]]
    feature_data: Sequence[PluginObjectFeatureData]

    @property
    def features(self) -> Sequence[PluginObjectFeature]:
        return [type_data.feature for type_data in self.feature_data]

    @overload
    def get_feature_data(self, feature: Literal["component"]) -> Optional[ComponentFeatureData]: ...

    @overload
    def get_feature_data(
        self, feature: Literal["scaffold-target"]
    ) -> Optional[ScaffoldTargetTypeData]: ...

    def get_feature_data(self, feature: PluginObjectFeature) -> Optional[PluginObjectFeatureData]:
        for feature_data in self.feature_data:
            if feature_data.feature == feature:
                return feature_data
        return None

    @property
    def scaffolder_schema(self) -> Optional[dict[str, Any]]:
        scaffolder_data = self.get_feature_data("scaffold-target")
        return scaffolder_data.schema if scaffolder_data else None

    @property
    def component_schema(self) -> Optional[dict[str, Any]]:
        component_data = self.get_feature_data("component")
        return component_data.schema if component_data else None
