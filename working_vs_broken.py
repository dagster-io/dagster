#!/usr/bin/env python3
"""
WORKING ALTERNATIVE: Shows what works vs what breaks

This demonstrates the difference between working and non-working approaches.
"""

import sys
sys.path.insert(0, '/workspaces/dagster/python_modules/dagster')

import dagster as dg
from pydantic import Field
from typing import Any

print("=== WORKING EXAMPLES ===")

# 1. Using regular default value - WORKS
class WorkingWithDefault(dg.Component, dg.Model, dg.Resolvable):
    config: dict[str, Any] = Field(default={})

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()

try:
    WorkingWithDefault.model()
    print("✓ WORKS: Field(default={})")
except Exception as e:
    print(f"✗ FAILS: Field(default={{}}) - {e}")

# 2. No field specification - WORKS
class WorkingWithoutField(dg.Component, dg.Model, dg.Resolvable):
    config: dict[str, Any] = {}

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()

try:
    WorkingWithoutField.model()
    print("✓ WORKS: config = {}")
except Exception as e:
    print(f"✗ FAILS: config = {{}} - {e}")

print("\n=== BROKEN EXAMPLE ===")

# 3. Using default_factory - BREAKS
class BrokenWithDefaultFactory(dg.Component, dg.Model, dg.Resolvable):
    config: dict[str, Any] = Field(default_factory=dict)

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()

try:
    BrokenWithDefaultFactory.model()
    print("✓ WORKS: Field(default_factory=dict)")
except Exception as e:
    print(f"✗ FAILS: Field(default_factory=dict) - {e}")

print("\n=== SUMMARY ===")
print("The issue occurs specifically with Field(default_factory=...) in Resolvable classes")
print("This is due to how derive_model_type handles field merging in base.py")