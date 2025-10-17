#!/usr/bin/env python3
"""
SIMULATE dg check defs COMMAND

This simulates what happens when you run `dg check defs` with the problematic component.
The error occurs during component discovery and registration.
"""

import sys
sys.path.insert(0, '/workspaces/dagster/python_modules/dagster')

import dagster as dg
from pydantic import Field
from typing import Any

# Create a component class that would be discovered by `dg check defs`
class TestComponent(dg.Component, dg.Model, dg.Resolvable):
    """This is the problematic component from the issue."""
    config: dict[str, Any] = Field(default_factory=dict)

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()

print("Component defined...")

# This simulates what happens during component discovery
# The error occurs in get_package_entry_snap -> _get_component_type_data -> obj.get_model_cls()
try:
    print("Calling get_model_cls() (simulates component discovery)...")
    model_cls = TestComponent.get_model_cls()
    print(f"Success: {model_cls}")
except Exception as e:
    print(f"FAILED with error: {type(e).__name__}: {e}")
    print("\nThis is exactly what causes 'dg check defs' to fail!")

# The call chain that leads to the error:
print("\n=== CALL CHAIN THAT LEADS TO ERROR ===")
print("1. dg check defs")
print("2. EnvRegistry.from_dg_context()")
print("3. _load_entry_point_registry_objects()")
print("4. list_plugins()")
print("5. get_package_entry_snap()")
print("6. _get_component_type_data()")
print("7. obj.get_model_cls()")
print("8. cls.model() [Component inherits from Resolvable]")
print("9. derive_model_type()")
print("10. FieldInfo.merge_field_infos() <- ERROR HERE")