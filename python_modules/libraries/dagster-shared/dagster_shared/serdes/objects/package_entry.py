import json
import textwrap
from abc import ABC, abstractmethod
from collections.abc import Sequence
from itertools import groupby
from typing import Any, Literal, Optional, TypedDict, overload

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
class EnvRegistryKey:
    namespace: str
    name: str

    @property
    def package(self) -> str:
        return self.namespace.split(".")[0]

    def to_typename(self) -> str:
        return f"{self.namespace}.{self.name}"

    @staticmethod
    def is_valid_typename(typename: str) -> bool:
        """Check if the typename is valid."""
        try:
            EnvRegistryKey.from_typename(typename)
            return True
        except ValueError:
            return False

    @staticmethod
    def from_typename(typename: str) -> "EnvRegistryKey":
        parts = typename.split(".")
        for part in parts:
            if not part.isidentifier():
                raise ValueError(_generate_invalid_component_typename_error_message(typename))
        if len(parts) < 2:
            raise ValueError(_generate_invalid_component_typename_error_message(typename))
        namespace, _, name = typename.rpartition(".")
        return EnvRegistryKey(name=name, namespace=namespace)


###########
# TYPE DATA
###########
EnvRegistryObjectFeature: TypeAlias = Literal["component", "scaffold-target"]


class EnvRegistryObjectFeatureData(ABC):
    @property
    @abstractmethod
    def feature(self) -> EnvRegistryObjectFeature:
        pass


@whitelist_for_serdes
@record
class ComponentFeatureData(EnvRegistryObjectFeatureData):
    schema: Optional[dict[str, Any]]

    @property
    def feature(self) -> EnvRegistryObjectFeature:
        return "component"


@whitelist_for_serdes
@record
class ScaffoldTargetTypeData(EnvRegistryObjectFeatureData):
    schema: Optional[dict[str, Any]]

    @property
    def feature(self) -> EnvRegistryObjectFeature:
        return "scaffold-target"


###############
# ENV REGISTRY MANIFEST
###############


@whitelist_for_serdes
@record
class EnvRegistryObjectSnap:
    key: EnvRegistryKey
    aliases: Sequence[EnvRegistryKey]
    summary: Optional[str]
    description: Optional[str]
    owners: Optional[Sequence[str]]
    tags: Optional[Sequence[str]]
    feature_data: Sequence[EnvRegistryObjectFeatureData]

    @property
    def features(self) -> Sequence[EnvRegistryObjectFeature]:
        return [type_data.feature for type_data in self.feature_data]

    @overload
    def get_feature_data(self, feature: Literal["component"]) -> Optional[ComponentFeatureData]: ...

    @overload
    def get_feature_data(
        self, feature: Literal["scaffold-target"]
    ) -> Optional[ScaffoldTargetTypeData]: ...

    def get_feature_data(
        self, feature: EnvRegistryObjectFeature
    ) -> Optional[EnvRegistryObjectFeatureData]:
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

    @property
    def is_component(self) -> bool:
        return self.get_feature_data("component") is not None

    @property
    def all_keys(self) -> Sequence[EnvRegistryKey]:
        """Return all keys associated with this plugin object, including aliases."""
        return [self.key, *self.aliases]


@whitelist_for_serdes
@record
class EnvRegistryManifest:
    """A manifest of all components in a package.

    This is used to generate the component registry and to validate that the package entry point
    is valid.
    """

    modules: Sequence[str]  # List of modules scanned
    objects: Sequence[EnvRegistryObjectSnap]

    def merge(self, other: "EnvRegistryManifest") -> "EnvRegistryManifest":
        """Merge another manifest with this one and return a new instance."""
        shared_modules = set(self.modules).intersection(other.modules)
        if shared_modules:
            raise ValueError(f"Cannot merge manifests with overlapping modules: {shared_modules}.")
        return EnvRegistryManifest(
            modules=[*self.modules, *other.modules],
            objects=[*self.objects, *other.objects],
        )


###################################
# COMPONENT REPRESENTATION FOR DOCS
###################################


class ComponentTypeJson(TypedDict):
    """Component type JSON, used to back dg docs webapp."""

    name: str
    owners: Optional[Sequence[str]]
    tags: Optional[Sequence[str]]
    example: str
    schema: str
    description: Optional[str]


class ComponentTypeNamespaceJson(TypedDict):
    """Component type namespace JSON, used to back dg docs webapp."""

    name: str
    componentTypes: list[ComponentTypeJson]


def json_for_all_components(
    components: Sequence[EnvRegistryObjectSnap],
) -> list[ComponentTypeNamespaceJson]:
    """Returns a list of JSON representations of all component types in the registry."""
    component_json = []
    for entry in components:
        key = entry.key
        component_type_data = entry.get_feature_data("component")
        if component_type_data:
            component_json.append(
                (
                    key.namespace.split(".")[0],
                    json_for_component_type(key, entry, component_type_data),
                )
            )
    return [
        ComponentTypeNamespaceJson(
            name=namespace,
            componentTypes=[namespace_and_component[1] for namespace_and_component in components],
        )
        for namespace, components in groupby(component_json, key=lambda x: x[0])
    ]


def json_for_component_type(
    key: EnvRegistryKey,
    entry: EnvRegistryObjectSnap,
    component_type_data: ComponentFeatureData,
) -> ComponentTypeJson:
    from dagster_shared.yaml_utils.sample_yaml import generate_sample_yaml

    typename = key.to_typename()
    sample_yaml = generate_sample_yaml(typename, component_type_data.schema or {})
    return ComponentTypeJson(
        name=typename,
        owners=entry.owners,
        tags=entry.tags,
        example=sample_yaml,
        schema=json.dumps(component_type_data.schema, sort_keys=True),
        description=entry.description,
    )
