#!/usr/bin/env python3
"""
MINIMAL REPRODUCTION: Pydantic Field default_factory Issue

This is the exact code that reproduces the issue described in the GitHub issue.
"""

import sys
sys.path.insert(0, '/workspaces/dagster/python_modules/dagster')

import dagster as dg
from pydantic import Field
from typing import Any

# This exact code causes the error:
class TestComponent(dg.Component, dg.Model, dg.Resolvable):
    config: dict[str, Any] = Field(default_factory=dict)

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()

# Trying to call .model() will trigger the error
try:
    TestComponent.model()
    print("SUCCESS: No error occurred")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    print("\n=== This is the exact issue described ===")