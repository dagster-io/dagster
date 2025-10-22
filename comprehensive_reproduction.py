#!/usr/bin/env python3
"""
Comprehensive script to reproduce the pydantic field issue.

This demonstrates the bug that occurs when a Pydantic BaseModel field with 
a default_factory is processed by the Dagster Resolvable derive_model_type function.

The problem is in python_modules/dagster/dagster/components/resolved/base.py 
around line 220 where FieldInfo.merge_field_infos is called.
"""

import sys
import os

# Add the dagster module to Python path
sys.path.insert(0, '/workspaces/dagster/python_modules/dagster')

try:
    import dagster as dg
    from pydantic import Field, BaseModel
    from typing import Any

    print("=== REPRODUCTION OF PYDANTIC FIELD ISSUE ===\n")

    print("1. Creating a working example (no default_factory)...")
    
    class WorkingComponent(dg.Component, BaseModel, dg.Resolvable):
        config: dict[str, Any] = Field(default={})  # This works - default value

        def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
            return dg.Definitions()
    
    try:
        model_cls = WorkingComponent.model()
        print(f"   ✓ Success: {model_cls}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")

    print("\n2. Creating a problematic example (with default_factory)...")
    
    class ProblematicComponent(dg.Component, BaseModel, dg.Resolvable):
        config: dict[str, Any] = Field(default_factory=dict)  # This causes the error

        def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
            return dg.Definitions()
    
    try:
        model_cls = ProblematicComponent.model()
        print(f"   ✓ Success: {model_cls}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")

    print("\n3. The error occurs because:")
    print("   - The original field has default_factory=dict")
    print("   - derive_model_type extracts field.default (PydanticUndefined) and field_info")
    print("   - It creates a new Field with default=_Unset")
    print("   - It tries to merge this with the original field_info that has default_factory")
    print("   - Pydantic raises 'cannot specify both default and default_factory'")

    print("\n=== ROOT CAUSE ANALYSIS ===")
    
    # Let's examine what happens step by step
    from dagster.components.resolved.base import _get_annotations
    
    print("\n4. Analyzing the problematic field annotations...")
    annotations = _get_annotations(ProblematicComponent)
    config_annotation = annotations['config']
    
    print(f"   Field type: {config_annotation.type}")
    print(f"   Has default: {config_annotation.has_default}")
    print(f"   Default value: {config_annotation.default}")
    print(f"   Field info: {config_annotation.field_info}")
    
    if config_annotation.field_info:
        print(f"   Field info default: {config_annotation.field_info.default}")
        print(f"   Field info default_factory: {config_annotation.field_info.default_factory}")

    print("\n=== HOW TO FIX ===")
    print("The issue is in derive_model_type around line 194-204:")
    print("When has_default=True and a field_info exists with default_factory,")
    print("the code should NOT create a new Field with default=_Unset")
    print("Instead, it should preserve the original default_factory behavior.")

except Exception as e:
    print(f"SETUP ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()