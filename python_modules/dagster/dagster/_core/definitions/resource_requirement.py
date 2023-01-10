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

from ..errors import DagsterInvalidDefinitionError
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


class TypeMaterializerResourceRequirement(
    NamedTuple("_TypeMaterializerResourceRequirement", [("key", str), ("type_display_name", str)]),
    ResourceRequirement,
):
    def describe_requirement(self) -> str:
        return (
            f"resource with key '{self.key}' required by the materializer on type"
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
    mode_name: Optional[str] = None,
) -> None:
    mode_descriptor = f" by mode '{mode_name}'" if mode_name and mode_name != "default" else ""
    for requirement in requirements:
        if requirement.resources_contain_key(
            resource_defs
        ) and not requirement.resource_is_expected_type(resource_defs):
            raise DagsterInvalidDefinitionError(
                f"{requirement.describe_requirement()}, but received"
                f" {type(resource_defs[requirement.key])}{mode_descriptor}."
            )


def ensure_requirements_satisfied(
    resource_defs: Mapping[str, "ResourceDefinition"],
    requirements: Sequence[ResourceRequirement],
    mode_name: Optional[str] = None,
) -> None:
    ensure_resources_of_expected_type(resource_defs, requirements, mode_name)

    mode_descriptor = f" by mode '{mode_name}'" if mode_name and mode_name != "default" else ""

    # Error if resource defs don't provide the correct resource key
    for requirement in requirements:
        if not requirement.resources_contain_key(resource_defs):
            raise DagsterInvalidDefinitionError(
                f"{requirement.describe_requirement()} was not provided{mode_descriptor}. Please"
                f" provide a {str(requirement.expected_type)} to key '{requirement.key}', or change"
                " the required key to one of the following keys which points to an"
                f" {str(requirement.expected_type)}:"
                f" {requirement.keys_of_expected_type(resource_defs)}"
            )


def get_resource_key_conflicts(
    resource_defs: Mapping[str, "ResourceDefinition"],
    other_resource_defs: Mapping[str, "ResourceDefinition"],
) -> AbstractSet[str]:
    overlapping_keys = set(resource_defs.keys()).intersection(set(other_resource_defs.keys()))
    overlapping_keys = {key for key in overlapping_keys if key != DEFAULT_IO_MANAGER_KEY}
    return overlapping_keys
