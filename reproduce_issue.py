#!/usr/bin/env python3
"""
Script to reproduce the issue where Pydantic fields with default_factory 
cause a TypeError when used with Resolvable classes.
"""

import sys
import os

# Add the dagster module to Python path
sys.path.insert(0, '/workspaces/dagster/python_modules/dagster')

try:
    import dagster as dg
    from pydantic import Field, BaseModel
    from typing import Any

    print("Creating TestComponent with Field(default_factory=dict)...")
    
    class TestComponent(dg.Component, BaseModel, dg.Resolvable):
        config: dict[str, Any] = Field(default_factory=dict)

        def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
            return dg.Definitions()
    
    print("Class defined successfully. Now attempting to call .model()...")
    
    # This should trigger the error
    model_cls = TestComponent.model()
    print(f"Model created successfully: {model_cls}")
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()