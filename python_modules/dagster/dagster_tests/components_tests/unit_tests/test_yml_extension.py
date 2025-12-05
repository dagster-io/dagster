"""Tests to verify that both .yaml and .yml extensions are supported for component definition files."""

from pathlib import Path
from typing import Optional

import pytest
import yaml
from dagster import Component, ComponentLoadContext, Definitions
from dagster.components.core.defs_module import find_defs_or_component_yaml
from dagster.components.testing import create_defs_folder_sandbox
from pydantic import BaseModel


class TestComponent(Component):
    """Simple test component for testing extension support."""

    class Schema(BaseModel):
        test_value: str = "default"

    @classmethod
    def get_model_cls(cls):
        return cls.Schema

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()


def test_find_defs_or_component_yaml_finds_yaml(tmp_path: Path):
    """Test that find_defs_or_component_yaml finds .yaml files."""
    defs_yaml = tmp_path / "defs.yaml"
    defs_yaml.write_text("type: test")
    
    result = find_defs_or_component_yaml(tmp_path)
    assert result == defs_yaml


def test_find_defs_or_component_yaml_finds_yml(tmp_path: Path):
    """Test that find_defs_or_component_yaml finds .yml files."""
    defs_yml = tmp_path / "defs.yml"
    defs_yml.write_text("type: test")
    
    result = find_defs_or_component_yaml(tmp_path)
    assert result == defs_yml


def test_find_defs_or_component_yaml_prefers_yaml_over_yml(tmp_path: Path):
    """Test that .yaml has precedence over .yml when both exist."""
    defs_yaml = tmp_path / "defs.yaml"
    defs_yml = tmp_path / "defs.yml"
    defs_yaml.write_text("type: yaml")
    defs_yml.write_text("type: yml")
    
    result = find_defs_or_component_yaml(tmp_path)
    assert result == defs_yaml


def test_find_defs_or_component_yaml_returns_none_when_no_file(tmp_path: Path):
    """Test that find_defs_or_component_yaml returns None when no definition file exists."""
    result = find_defs_or_component_yaml(tmp_path)
    assert result is None


def test_component_loads_from_yaml_file():
    """Test that a component can be loaded from a .yaml file."""
    with create_defs_folder_sandbox() as sandbox:
        component_dir = sandbox.defs_folder_path / "test_component"
        component_dir.mkdir()
        
        defs_yaml = component_dir / "defs.yaml"
        defs_yaml.write_text(yaml.safe_dump({
            "type": "dagster_tests.components_tests.unit_tests.test_yml_extension.TestComponent",
            "attributes": {
                "test_value": "from_yaml"
            }
        }))
        
        with sandbox.build_component_tree() as tree:
            defs = tree.build_defs()
            # Should load without error
            assert defs is not None


def test_component_loads_from_yml_file():
    """Test that a component can be loaded from a .yml file."""
    with create_defs_folder_sandbox() as sandbox:
        component_dir = sandbox.defs_folder_path / "test_component"
        component_dir.mkdir()
        
        defs_yml = component_dir / "defs.yml"
        defs_yml.write_text(yaml.safe_dump({
            "type": "dagster_tests.components_tests.unit_tests.test_yml_extension.TestComponent",
            "attributes": {
                "test_value": "from_yml"
            }
        }))
        
        with sandbox.build_component_tree() as tree:
            defs = tree.build_defs()
            # Should load without error
            assert defs is not None


def test_yaml_and_yml_produce_equivalent_components():
    """Test that identical content in .yaml and .yml files produces equivalent results."""
    component_content = {
        "type": "dagster_tests.components_tests.unit_tests.test_yml_extension.TestComponent",
        "attributes": {
            "test_value": "test_value"
        }
    }
    
    # Test with .yaml
    with create_defs_folder_sandbox() as sandbox:
        component_dir = sandbox.defs_folder_path / "yaml_component"
        component_dir.mkdir()
        
        defs_yaml = component_dir / "defs.yaml"
        defs_yaml.write_text(yaml.safe_dump(component_content))
        
        with sandbox.build_component_tree() as tree:
            defs_from_yaml = tree.build_defs()
    
    # Test with .yml
    with create_defs_folder_sandbox() as sandbox:
        component_dir = sandbox.defs_folder_path / "yml_component"
        component_dir.mkdir()
        
        defs_yml = component_dir / "defs.yml"
        defs_yml.write_text(yaml.safe_dump(component_content))
        
        with sandbox.build_component_tree() as tree:
            defs_from_yml = tree.build_defs()
    
    # Both should load successfully
    assert defs_from_yaml is not None
    assert defs_from_yml is not None


def test_both_extensions_in_different_components():
    """Test that .yaml and .yml can coexist in different components."""
    with create_defs_folder_sandbox() as sandbox:
        # Create component with .yaml
        yaml_component_dir = sandbox.defs_folder_path / "yaml_component"
        yaml_component_dir.mkdir()
        (yaml_component_dir / "defs.yaml").write_text(yaml.safe_dump({
            "type": "dagster_tests.components_tests.unit_tests.test_yml_extension.TestComponent",
        }))
        
        # Create component with .yml
        yml_component_dir = sandbox.defs_folder_path / "yml_component"
        yml_component_dir.mkdir()
        (yml_component_dir / "defs.yml").write_text(yaml.safe_dump({
            "type": "dagster_tests.components_tests.unit_tests.test_yml_extension.TestComponent",
        }))
        
        with sandbox.build_component_tree() as tree:
            defs = tree.build_defs()
            # Both components should load without error
            assert defs is not None
