from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, AbstractSet, Optional  # noqa: UP035

from dagster._core.definitions.utils import DEFAULT_IO_MANAGER_KEY
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvalidInvocationError
from dagster._record import record
from dagster._utils.merger import merge_dicts

if TYPE_CHECKING:
    from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
    from dagster._core.definitions.resource_definition import ResourceDefinition


class ResourceRequirement(ABC):
    @property
    def expected_type(self) -> type:
        from dagster._core.definitions.resource_definition import ResourceDefinition

        return ResourceDefinition

    @property
    def is_io_manager_requirement(self) -> bool:
        from dagster._core.storage.io_manager import IInputManagerDefinition, IOManagerDefinition

        return (
            self.expected_type == IOManagerDefinition
            or self.expected_type == IInputManagerDefinition
        )

    def keys_of_expected_type(
        self, resource_defs: Mapping[str, "ResourceDefinition"]
    ) -> Sequence[str]:
        """Get resource keys that correspond to resource definitions of expected type.

        For example, if this particular ResourceRequirement subclass required an ``IOManagerDefinition``, this method would vend all keys that corresponded to ``IOManagerDefinition``s.
        """
        return [
            resource_key
            for resource_key, resource_def in resource_defs.items()
            if isinstance(resource_def, self.expected_type)
        ]

    @abstractmethod
    def is_satisfied(self, resource_defs: Mapping[str, "ResourceDefinition"]) -> bool: ...

    @abstractmethod
    def ensure_satisfied(self, resource_defs: Mapping[str, "ResourceDefinition"]): ...


class ResourceKeyRequirement(ResourceRequirement, ABC):
    @property
    @abstractmethod
    def key(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def describe_requirement(self) -> str:
        raise NotImplementedError()

    def is_satisfied(self, resource_defs: Mapping[str, "ResourceDefinition"]) -> bool:
        return self.key in resource_defs and isinstance(resource_defs[self.key], self.expected_type)

    def ensure_satisfied(self, resource_defs: Mapping[str, "ResourceDefinition"]):
        requirement_expected_type_name = self.expected_type.__name__
        if self.key not in resource_defs:
            raise DagsterInvalidDefinitionError(
                f"{self.describe_requirement()} was not provided. Please"
                f" provide a {requirement_expected_type_name} to key '{self.key}', or change"
                " the required key to one of the following keys which points to an"
                f" {requirement_expected_type_name}:"
                f" {self.keys_of_expected_type(resource_defs)}"
            )
        resource_def = resource_defs[self.key]
        if not isinstance(resource_def, self.expected_type):
            raise DagsterInvalidDefinitionError(
                f"{self.describe_requirement()}, but received {type(resource_def)}."
            )


class ResourceAddable(ABC):
    @abstractmethod
    def with_resources(
        self, resource_defs: Mapping[str, "ResourceDefinition"]
    ) -> "ResourceAddable":
        raise NotImplementedError()


@record
class OpDefinitionResourceRequirement(ResourceKeyRequirement):
    key: str  # pyright: ignore[reportIncompatibleMethodOverride]
    node_description: str

    def describe_requirement(self) -> str:
        return f"resource with key '{self.key}' required by {self.node_description}"


@record
class InputManagerRequirement(ResourceKeyRequirement):
    key: str  # pyright: ignore[reportIncompatibleMethodOverride]
    node_description: str
    input_name: str
    root_input: bool

    @property
    def expected_type(self) -> type:
        from dagster._core.storage.io_manager import IInputManagerDefinition

        return IInputManagerDefinition

    def describe_requirement(self) -> str:
        return (
            f"input manager with key '{self.key}' required by input '{self.input_name}' of"
            f" {self.node_description}"
        )


# The ResourceRequirement for unexecutable external assets. Is an analogue to
# `SourceAssetIOManagerRequirement`.
@record
class ExternalAssetIOManagerRequirement(ResourceKeyRequirement):
    key: str  # pyright: ignore[reportIncompatibleMethodOverride]
    asset_key: Optional[str]

    @property
    def expected_type(self) -> type:
        from dagster._core.storage.io_manager import IOManagerDefinition

        return IOManagerDefinition

    def describe_requirement(self) -> str:
        external_asset_descriptor = (
            f"external asset with key {self.asset_key}" if self.asset_key else "external asset"
        )
        return f"io manager with key '{self.key}' required by {external_asset_descriptor}"


@record
class SourceAssetIOManagerRequirement(ResourceKeyRequirement):
    key: str  # pyright: ignore[reportIncompatibleMethodOverride]
    asset_key: Optional[str]

    @property
    def expected_type(self) -> type:
        from dagster._core.storage.io_manager import IOManagerDefinition

        return IOManagerDefinition

    def describe_requirement(self) -> str:
        source_asset_descriptor = (
            f"SourceAsset with key {self.asset_key}" if self.asset_key else "SourceAsset"
        )
        return f"io manager with key '{self.key}' required by {source_asset_descriptor}"


@record
class OutputManagerRequirement(ResourceKeyRequirement):
    key: str  # pyright: ignore[reportIncompatibleMethodOverride]
    node_description: str
    output_name: str

    @property
    def expected_type(self) -> type:
        from dagster._core.storage.io_manager import IOManagerDefinition

        return IOManagerDefinition

    def describe_requirement(self) -> str:
        return (
            f"io manager with key '{self.key}' required by output '{self.output_name}' of"
            f" {self.node_description}'"
        )


@record
class HookResourceRequirement(ResourceKeyRequirement):
    key: str  # pyright: ignore[reportIncompatibleMethodOverride]
    attached_to: Optional[str]
    hook_name: str

    def describe_requirement(self) -> str:
        attached_to_desc = f"attached to {self.attached_to}" if self.attached_to else ""
        return (
            f"resource with key '{self.key}' required by hook '{self.hook_name}' {attached_to_desc}"
        )


@record
class TypeResourceRequirement(ResourceKeyRequirement):
    key: str  # pyright: ignore[reportIncompatibleMethodOverride]
    type_display_name: str

    def describe_requirement(self) -> str:
        return f"resource with key '{self.key}' required by type '{self.type_display_name}'"


@record
class TypeLoaderResourceRequirement(ResourceKeyRequirement):
    key: str  # pyright: ignore[reportIncompatibleMethodOverride]
    type_display_name: str

    def describe_requirement(self) -> str:
        return (
            f"resource with key '{self.key}' required by the loader on type"
            f" '{self.type_display_name}'"
        )


@record
class ResourceDependencyRequirement(ResourceKeyRequirement):
    key: str  # pyright: ignore[reportIncompatibleMethodOverride]
    source_key: Optional[str]

    def describe_requirement(self) -> str:
        source_descriptor = f" by resource with key '{self.source_key}'" if self.source_key else ""
        return f"resource with key '{self.key}' required{source_descriptor}"


def ensure_requirements_satisfied(
    resource_defs: Mapping[str, "ResourceDefinition"],
    requirements: Sequence[ResourceRequirement],
) -> None:
    for requirement in requirements:
        requirement.ensure_satisfied(resource_defs)


def get_resource_key_conflicts(
    resource_defs: Mapping[str, "ResourceDefinition"],
    other_resource_defs: Mapping[str, "ResourceDefinition"],
) -> AbstractSet[str]:
    overlapping_keys = set(resource_defs.keys()).intersection(set(other_resource_defs.keys()))
    overlapping_keys = {key for key in overlapping_keys if key != DEFAULT_IO_MANAGER_KEY}
    return overlapping_keys


def merge_resource_defs(
    old_resource_defs: Mapping[str, "ResourceDefinition"],
    resource_defs_to_merge_in: Mapping[str, "ResourceDefinition"],
    requires_resources: "AssetsDefinition",
) -> Mapping[str, "ResourceDefinition"]:
    from dagster._core.execution.resources_init import get_transitive_required_resource_keys

    overlapping_keys = get_resource_key_conflicts(old_resource_defs, resource_defs_to_merge_in)
    if overlapping_keys:
        overlapping_keys_str = ", ".join(sorted(list(overlapping_keys)))
        raise DagsterInvalidInvocationError(
            f"{requires_resources} has conflicting resource "
            "definitions with provided resources for the following keys: "
            f"{overlapping_keys_str}. Either remove the existing "
            "resources from the asset or change the resource keys so that "
            "they don't overlap."
        )

    merged_resource_defs = merge_dicts(resource_defs_to_merge_in, old_resource_defs)

    # Ensure top-level resource requirements are met - except for
    # io_manager, since that is a default it can be resolved later.
    requirements = [
        *requires_resources.get_resource_requirements(),
        *[
            req
            for key, resource in merged_resource_defs.items()
            for req in resource.get_resource_requirements(source_key=key)
        ],
    ]
    ensure_requirements_satisfied(merged_resource_defs, requirements)

    # Get all transitive resource dependencies from other resources.
    relevant_keys = get_transitive_required_resource_keys(
        requires_resources.required_resource_keys, merged_resource_defs
    )
    return {
        key: resource_def
        for key, resource_def in merged_resource_defs.items()
        if key in relevant_keys
    }
