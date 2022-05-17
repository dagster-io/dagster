from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AbstractSet, Iterator, List, Mapping, NamedTuple, Optional, Type

from ..errors import DagsterInvalidDefinitionError

if TYPE_CHECKING:
    from ..types.dagster_type import DagsterType
    from .dependency import Node, NodeHandle
    from .pipeline_definition import PipelineDefinition
    from .resource_definition import ResourceDefinition
    from .solid_definition import SolidDefinition


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

    def keys_of_expected_type(self, resource_defs: Mapping[str, "ResourceDefinition"]) -> List[str]:
        return [
            resource_key
            for resource_key, resource_def in resource_defs.items()
            if isinstance(resource_def, self.expected_type)
        ]

    def requirement_satisfied(
        self,
        resource_defs: Mapping[str, "ResourceDefinition"],
        mode_name: Optional[str] = None,
        error_if_unsatisfied: bool = True,
    ) -> bool:
        # Always error if resource type mismatches
        if self.key in resource_defs and not isinstance(
            resource_defs[self.key], self.expected_type
        ):
            raise DagsterInvalidDefinitionError(
                f"{self.describe_requirement()}, but received {type(resource_defs[self.key])}."
            )

        # Conditionally error if resource defs don't provide the correct resource key
        if self.key not in resource_defs:
            if error_if_unsatisfied:
                mode_descriptor = (
                    f" by mode '{mode_name}'" if mode_name and mode_name != "default" else ""
                )
                raise DagsterInvalidDefinitionError(
                    f"{self.describe_requirement()} was not provided{mode_descriptor}. Please provide a {str(self.expected_type)} to key '{self.key}', or change the required key to one of the following keys which points to an {str(self.expected_type)}: {self.keys_of_expected_type(resource_defs)}"
                )
            return False
        return True


class SolidDefinitionResourceRequirement(
    NamedTuple("_SolidDefinitionResourceRequirement", [("key", str), ("node_description", str)]),
    ResourceRequirement,
):
    def describe_requirement(self) -> str:
        return f"resource with key '{self.key}' required by {self.node_description}"


class InputManagerRequirement(
    NamedTuple(
        "_InputManagerRequirement", [("key", str), ("node_description", str), ("input_name", str)]
    ),
    ResourceRequirement,
):
    @property
    def expected_type(self) -> Type:
        from ..storage.io_manager import IInputManagerDefinition

        return IInputManagerDefinition

    def describe_requirement(self) -> str:
        return f"input manager with key '{self.key}' required by input '{self.input_name}' of {self.node_description}"


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
        return f"io manager with key '{self.key}' required by output '{self.output_name}' of {self.node_description}'"


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
        return f"resource with key '{self.key}' required by the loader on type '{self.type_display_name}'"


class TypeMaterializerResourceRequirement(
    NamedTuple("_TypeMaterializerResourceRequirement", [("key", str), ("type_display_name", str)]),
    ResourceRequirement,
):
    def describe_requirement(self) -> str:
        return f"resource with key '{self.key}' required by the materializer on type '{self.type_display_name}'"


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
