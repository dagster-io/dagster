from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Iterator,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Type,
)

from dagster._utils.merger import merge_dicts

from ..errors import DagsterInvalidDefinitionError, DagsterInvalidInvocationError
from .utils import DEFAULT_IO_MANAGER_KEY

if TYPE_CHECKING:
    from .resource_definition import ResourceDefinition


class ResourceRequirement(ABC):
    @property
    @abstractmethod
    def key(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def describe_requirement(self) -> str:
        raise NotImplementedError()

    @property
    def expected_type(self) -> Type:
        from .resource_definition import ResourceDefinition

        return ResourceDefinition

    @property
    def is_io_manager_requirement(self) -> bool:
        from ..storage.io_manager import IInputManagerDefinition, IOManagerDefinition

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

    def resource_is_expected_type(self, resource_defs: Mapping[str, "ResourceDefinition"]) -> bool:
        # Expects resource key to be in resource_defs
        return isinstance(resource_defs[self.key], self.expected_type)

    def resources_contain_key(
        self,
        resource_defs: Mapping[str, "ResourceDefinition"],
    ) -> bool:
        return self.key in resource_defs


class ResourceAddable(ABC):
    @abstractmethod
    def with_resources(
        self, resource_defs: Mapping[str, "ResourceDefinition"]
    ) -> "ResourceAddable":
        raise NotImplementedError()


class OpDefinitionResourceRequirement(
    NamedTuple("_OpDefinitionResourceRequirement", [("key", str), ("node_description", str)]),
    ResourceRequirement,
):
    def describe_requirement(self) -> str:
        return f"resource with key '{self.key}' required by {self.node_description}"


class InputManagerRequirement(
    NamedTuple(
        "_InputManagerRequirement",
        [("key", str), ("node_description", str), ("input_name", str), ("root_input", bool)],
    ),
    ResourceRequirement,
):
    @property
    def expected_type(self) -> Type:
        from ..storage.io_manager import IInputManagerDefinition

        return IInputManagerDefinition

    def describe_requirement(self) -> str:
        return (
            f"input manager with key '{self.key}' required by input '{self.input_name}' of"
            f" {self.node_description}"
        )


class SourceAssetIOManagerRequirement(
    NamedTuple(
        "_InputManagerRequirement",
        [
            ("key", str),
            ("asset_key", Optional[str]),
        ],
    ),
    ResourceRequirement,
):
    @property
    def expected_type(self) -> Type:
        from ..storage.io_manager import IOManagerDefinition

        return IOManagerDefinition

    def describe_requirement(self) -> str:
        source_asset_descriptor = (
            f"SourceAsset with key {self.asset_key}" if self.asset_key else "SourceAsset"
        )
        return f"io manager with key '{self.key}' required by {source_asset_descriptor}"


class OutputManagerRequirement(
    NamedTuple(
        "_OutputManagerRequirement", [("key", str), ("node_description", str), ("output_name", str)]
    ),
    ResourceRequirement,
):
    @property
    def expected_type(self) -> Type:
        from ..storage.io_manager import IOManagerDefinition

        return IOManagerDefinition

    def describe_requirement(self) -> str:
        return (
            f"io manager with key '{self.key}' required by output '{self.output_name}' of"
            f" {self.node_description}'"
        )


class HookResourceRequirement(
    NamedTuple(
        "_HookResourceRequirement",
        [("key", str), ("attached_to", Optional[str]), ("hook_name", str)],
    ),
    ResourceRequirement,
):
    def describe_requirement(self) -> str:
        attached_to_desc = f"attached to {self.attached_to}" if self.attached_to else ""
        return (
            f"resource with key '{self.key}' required by hook '{self.hook_name}' {attached_to_desc}"
        )


class TypeResourceRequirement(
    NamedTuple("_TypeResourceRequirement", [("key", str), ("type_display_name", str)]),
    ResourceRequirement,
):
    def describe_requirement(self) -> str:
        return f"resource with key '{self.key}' required by type '{self.type_display_name}'"


class TypeLoaderResourceRequirement(
    NamedTuple("_TypeLoaderResourceRequirement", [("key", str), ("type_display_name", str)]),
    ResourceRequirement,
):
    def describe_requirement(self) -> str:
        return (
            f"resource with key '{self.key}' required by the loader on type"
            f" '{self.type_display_name}'"
        )


class ResourceDependencyRequirement(
    NamedTuple("_ResourceDependencyRequirement", [("key", str), ("source_key", Optional[str])]),
    ResourceRequirement,
):
    def describe_requirement(self) -> str:
        source_descriptor = f" by resource with key '{self.source_key}'" if self.source_key else ""
        return f"resource with key '{self.key}' required{source_descriptor}"


class RequiresResources(ABC):
    @property
    @abstractmethod
    def required_resource_keys(self) -> AbstractSet[str]:
        raise NotImplementedError()

    @abstractmethod
    def get_resource_requirements(
        self, outer_context: Optional[object] = None
    ) -> Iterator[ResourceRequirement]:
        raise NotImplementedError()


def ensure_resources_of_expected_type(
    resource_defs: Mapping[str, "ResourceDefinition"],
    requirements: Sequence[ResourceRequirement],
) -> None:
    for requirement in requirements:
        if requirement.resources_contain_key(
            resource_defs
        ) and not requirement.resource_is_expected_type(resource_defs):
            raise DagsterInvalidDefinitionError(
                f"{requirement.describe_requirement()}, but received"
                f" {type(resource_defs[requirement.key])}."
            )


def ensure_requirements_satisfied(
    resource_defs: Mapping[str, "ResourceDefinition"],
    requirements: Sequence[ResourceRequirement],
) -> None:
    ensure_resources_of_expected_type(resource_defs, requirements)

    # Error if resource defs don't provide the correct resource key
    for requirement in requirements:
        if not requirement.resources_contain_key(resource_defs):
            requirement_expected_type_name = requirement.expected_type.__name__
            raise DagsterInvalidDefinitionError(
                f"{requirement.describe_requirement()} was not provided. Please"
                f" provide a {requirement_expected_type_name} to key '{requirement.key}', or change"
                " the required key to one of the following keys which points to an"
                f" {requirement_expected_type_name}:"
                f" {requirement.keys_of_expected_type(resource_defs)}"
            )


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
    requires_resources: RequiresResources,
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
    ensure_requirements_satisfied(
        merged_resource_defs, list(requires_resources.get_resource_requirements())
    )

    # Get all transitive resource dependencies from other resources.
    relevant_keys = get_transitive_required_resource_keys(
        requires_resources.required_resource_keys, merged_resource_defs
    )
    return {
        key: resource_def
        for key, resource_def in merged_resource_defs.items()
        if key in relevant_keys
    }
