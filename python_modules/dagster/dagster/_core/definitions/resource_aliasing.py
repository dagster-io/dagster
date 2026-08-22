"""
Utilities for resource key aliasing/renaming functionality.

This module provides helper functions to remap resource keys in various definition types
to support the rename_resources API as requested in issue #29254.
"""

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, AbstractSet, Type, TypeVar

import dagster._check as check
from dagster._record import record

from .resource_requirement import (
    ExternalAssetIOManagerRequirement,
    HookResourceRequirement,
    InputManagerRequirement,
    OpDefinitionResourceRequirement,
    OutputManagerRequirement,
    ResourceDependencyRequirement,
    ResourceKeyRequirement,
    ResourceRequirement,
    SourceAssetIOManagerRequirement,
    TypeLoaderResourceRequirement,
    TypeResourceRequirement,
)

if TYPE_CHECKING:
    from .hook_definition import HookDefinition
    from .node_definition import NodeDefinition
    from .op_definition import OpDefinition

T = TypeVar("T", bound=ResourceKeyRequirement)


def remap_resource_key_in_requirement(
    requirement: T, resource_mapping: Mapping[str, str]
) -> T:
    """
    Remap the resource key in a ResourceKeyRequirement according to the provided mapping.
    
    Args:
        requirement: The resource requirement to remap
        resource_mapping: Mapping from old resource key to new resource key
        
    Returns:
        New requirement instance with remapped key, or original if no mapping needed
    """
    old_key = requirement.key
    new_key = resource_mapping.get(old_key, old_key)
    
    if new_key == old_key:
        return requirement
    
    # Create a new instance with the remapped key using the record pattern
    if isinstance(requirement, OpDefinitionResourceRequirement):
        return OpDefinitionResourceRequirement(
            key=new_key,
            node_description=requirement.node_description,
        )
    elif isinstance(requirement, InputManagerRequirement):
        return InputManagerRequirement(
            key=new_key,
            node_description=requirement.node_description,
            input_name=requirement.input_name,
            root_input=requirement.root_input,
        )
    elif isinstance(requirement, OutputManagerRequirement):
        return OutputManagerRequirement(
            key=new_key,
            node_description=requirement.node_description,
            output_name=requirement.output_name,
        )
    elif isinstance(requirement, HookResourceRequirement):
        return HookResourceRequirement(
            key=new_key,
            attached_to=requirement.attached_to,
            hook_name=requirement.hook_name,
        )
    elif isinstance(requirement, SourceAssetIOManagerRequirement):
        return SourceAssetIOManagerRequirement(
            key=new_key,
            asset_key=requirement.asset_key,
        )
    elif isinstance(requirement, ExternalAssetIOManagerRequirement):
        return ExternalAssetIOManagerRequirement(
            key=new_key,
            asset_key=requirement.asset_key,
        )
    elif isinstance(requirement, TypeResourceRequirement):
        return TypeResourceRequirement(
            key=new_key,
            type_display_name=requirement.type_display_name,
        )
    elif isinstance(requirement, TypeLoaderResourceRequirement):
        return TypeLoaderResourceRequirement(
            key=new_key,
            type_display_name=requirement.type_display_name,
        )
    elif isinstance(requirement, ResourceDependencyRequirement):
        return ResourceDependencyRequirement(
            key=new_key,
            source_key=requirement.source_key,
        )
    else:
        # Fallback for any new requirement types - this should not normally happen
        # but provides a safety net for extensibility
        raise NotImplementedError(
            f"Resource key remapping not implemented for requirement type: {type(requirement)}"
        )


def remap_resource_keys_in_requirements(
    requirements: Sequence[ResourceRequirement], 
    resource_mapping: Mapping[str, str]
) -> Sequence[ResourceRequirement]:
    """
    Remap resource keys in a sequence of ResourceRequirements.
    
    Args:
        requirements: Sequence of requirements to process
        resource_mapping: Mapping from old resource key to new resource key
        
    Returns:
        New sequence with remapped requirements
    """
    if not resource_mapping:
        return requirements
        
    remapped_requirements = []
    for req in requirements:
        if isinstance(req, ResourceKeyRequirement):
            remapped_requirements.append(remap_resource_key_in_requirement(req, resource_mapping))
        else:
            # Non-key requirements pass through unchanged
            remapped_requirements.append(req)
    
    return remapped_requirements


def remap_resource_keys_in_set(
    resource_keys: AbstractSet[str], 
    resource_mapping: Mapping[str, str]
) -> AbstractSet[str]:
    """
    Remap resource keys in a set according to the provided mapping.
    
    Args:
        resource_keys: Set of resource keys to remap
        resource_mapping: Mapping from old resource key to new resource key
        
    Returns:
        New set with remapped keys
    """
    if not resource_mapping:
        return resource_keys
        
    return {resource_mapping.get(key, key) for key in resource_keys}


def validate_resource_mapping(
    resource_mapping: Mapping[str, str],
    available_resources: AbstractSet[str]
) -> None:
    """
    Validate that a resource mapping is valid.
    
    Args:
        resource_mapping: Mapping from old resource key to new resource key
        available_resources: Set of available resource keys after mapping
        
    Raises:
        DagsterInvalidInvocationError: If the mapping is invalid
    """
    from dagster._core.errors import DagsterInvalidInvocationError
    
    resource_mapping = check.mapping_param(resource_mapping, "resource_mapping", key_type=str, value_type=str)
    
    # Check for self-mapping (old_key -> old_key) which is redundant but not harmful
    for old_key, new_key in resource_mapping.items():
        if old_key == new_key:
            continue
            
    # Check that new keys don't conflict with existing keys that are already a target of another mapping
        if (
            old_key in available_resources
            and new_key in available_resources
            and any(
                other_old != old_key and new_key == other_new
                for other_old, other_new in resource_mapping.items()
            )
        ):
            raise DagsterInvalidInvocationError(
                f"Cannot rename resource '{old_key}' to '{new_key}' because '{new_key}' is already the target of another resource mapping. This would create a conflict."

            )
    
    # Check for circular mappings (A->B, B->A)
    visited = set()
    for start_key in resource_mapping:
        if start_key in visited:
            continue
            
        path = []
        current = start_key
        while current in resource_mapping:
            if current in path:
                cycle = " -> ".join(path + [current])
                raise DagsterInvalidInvocationError(
                    f"Circular resource mapping detected: {cycle}"
                )
            path.append(current)
            visited.add(current)
            current = resource_mapping[current]