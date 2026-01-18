"""Tests for the YAML template generator functionality."""

from pathlib import Path

import dagster as dg
import pytest
from dagster_dg_cli.utils.yaml_template_generator import (
    generate_defs_yaml_example_values,
    generate_defs_yaml_schema,
)
from dagster_fivetran.components.workspace_component.component import FivetranAccountComponent
from dagster_shared import seven
from dagster_sling.components.sling_replication_collection.component import (
    SlingReplicationCollectionComponent,
)


class TestYamlTemplateGenerator:
    @property
    def test_data_dir(self) -> Path:
        """Get the test data directory path."""
        return Path(__file__).parent / "test_data"

    def load_expected_schema(self, test_case_name: str) -> str:
        """Load expected schema template from disk for a given test case."""
        expected_file = self.test_data_dir / test_case_name / "expected_schema"
        return expected_file.read_text().strip()

    def load_expected_example(self, test_case_name: str) -> str:
        """Load expected example values from disk for a given test case."""
        expected_file = self.test_data_dir / test_case_name / "expected_example"
        return expected_file.read_text().strip()

    def get_component_schema(self, component_class) -> dict:
        """Generate JSON schema from a component class."""
        model_cls = component_class.get_model_cls()
        schema = model_cls.model_json_schema()
        return schema

    def test_simple_pipes_script_component_template(self):
        """Test generation of SimplePipesScriptComponent template using actual component class."""
        from dagster_test.components import SimplePipesScriptComponent

        # Get schema from the actual component class
        schema = self.get_component_schema(SimplePipesScriptComponent)

        # Test schema generation
        schema_result = generate_defs_yaml_schema(
            "dagster_test.components.simple_pipes_script_asset.SimplePipesScriptComponent", schema
        )
        expected_schema = self.load_expected_schema("simple_example")
        assert schema_result.strip() == expected_schema, (
            f"Generated schema does not match expected output.\n\nGenerated:\n{schema_result}\n\nExpected:\n{expected_schema}"
        )

        # Test example values generation
        example_result = generate_defs_yaml_example_values(
            "dagster_test.components.simple_pipes_script_asset.SimplePipesScriptComponent", schema
        )
        expected_example = self.load_expected_example("simple_example")
        assert example_result.strip() == expected_example, (
            f"Generated example values do not match expected output.\n\nGenerated:\n{example_result}\n\nExpected:\n{expected_example}"
        )

    def test_defs_folder_component_template(self):
        """Test generation of DefsFolderComponent template using actual component class."""
        # Get schema from the actual component class
        schema = self.get_component_schema(dg.DefsFolderComponent)

        # Test schema generation
        schema_result = generate_defs_yaml_schema("dagster.DefsFolderComponent", schema)
        expected_schema = self.load_expected_schema("defs_folder")
        assert schema_result.strip() == expected_schema, (
            f"Generated schema does not match expected output.\n\nGenerated:\n{schema_result}\n\nExpected:\n{expected_schema}"
        )

        # Test example values generation
        example_result = generate_defs_yaml_example_values("dagster.DefsFolderComponent", schema)
        expected_example = self.load_expected_example("defs_folder")
        assert example_result.strip() == expected_example, (
            f"Generated example values do not match expected output.\n\nGenerated:\n{example_result}\n\nExpected:\n{expected_example}"
        )

    def test_fivetran_account_component_template(self):
        """Test generation of FivetranAccountComponent template using actual component class."""
        # Get schema from the actual component class
        schema = self.get_component_schema(FivetranAccountComponent)

        # Test schema generation
        schema_result = generate_defs_yaml_schema(
            "dagster_fivetran.FivetranAccountComponent", schema
        )
        expected_schema = self.load_expected_schema("account")
        assert schema_result.strip() == expected_schema, (
            f"Generated schema does not match expected output.\n\nGenerated:\n{schema_result}\n\nExpected:\n{expected_schema}"
        )

        # Test example values generation
        example_result = generate_defs_yaml_example_values(
            "dagster_fivetran.FivetranAccountComponent", schema
        )
        expected_example = self.load_expected_example("account")
        assert example_result.strip() == expected_example, (
            f"Generated example values do not match expected output.\n\nGenerated:\n{example_result}\n\nExpected:\n{expected_example}"
        )

    def test_python_script_component_template(self):
        """Test generation of PythonScriptComponent template using actual component class."""
        # Get schema from the actual component class
        schema = self.get_component_schema(dg.PythonScriptComponent)

        # Test schema generation
        schema_result = generate_defs_yaml_schema("dagster.PythonScriptComponent", schema)
        expected_schema = self.load_expected_schema("python_script")
        assert schema_result.strip() == expected_schema, (
            f"Generated schema does not match expected output.\n\nGenerated:\n{schema_result}\n\nExpected:\n{expected_schema}"
        )

        # Test example values generation
        example_result = generate_defs_yaml_example_values("dagster.PythonScriptComponent", schema)
        expected_example = self.load_expected_example("python_script")
        assert example_result.strip() == expected_example, (
            f"Generated example values do not match expected output.\n\nGenerated:\n{example_result}\n\nExpected:\n{expected_example}"
        )

    def test_sling_replication_collection_component_template(self):
        """Test generation of SlingReplicationCollectionComponent template using actual component class."""
        # Get schema from the actual component class
        schema = self.get_component_schema(SlingReplicationCollectionComponent)

        # Test schema generation
        schema_result = generate_defs_yaml_schema(
            "dagster_sling.SlingReplicationCollectionComponent", schema
        )
        expected_schema = self.load_expected_schema("sling_replication_collection")
        assert schema_result.strip() == expected_schema, (
            f"Generated schema does not match expected output.\n\nGenerated:\n{schema_result}\n\nExpected:\n{expected_schema}"
        )

        # Test example values generation
        example_result = generate_defs_yaml_example_values(
            "dagster_sling.SlingReplicationCollectionComponent", schema
        )
        expected_example = self.load_expected_example("sling_replication_collection")
        assert example_result.strip() == expected_example, (
            f"Generated example values do not match expected output.\n\nGenerated:\n{example_result}\n\nExpected:\n{expected_example}"
        )

    def test_dbt_project_component_template(self):
        """Test generation of DbtProjectComponent template using actual component class."""
        # Get schema from the actual component class
        # dbt-core doesn't support Python 3.14
        if seven.IS_PYTHON_3_14:
            pytest.skip("dbt-core doesn't support Python 3.14")

        from dagster_dbt.components.dbt_project.component import DbtProjectComponent

        schema = self.get_component_schema(DbtProjectComponent)

        # Test schema generation
        schema_result = generate_defs_yaml_schema("dagster_dbt.DbtProjectComponent", schema)
        expected_schema = self.load_expected_schema("dbt_project")
        assert schema_result.strip() == expected_schema, (
            f"Generated schema does not match expected output.\n\nGenerated:\n{schema_result}\n\nExpected:\n{expected_schema}"
        )

        # Test example values generation
        example_result = generate_defs_yaml_example_values(
            "dagster_dbt.DbtProjectComponent", schema
        )
        expected_example = self.load_expected_example("dbt_project")
        assert example_result.strip() == expected_example, (
            f"Generated example values do not match expected output.\n\nGenerated:\n{example_result}\n\nExpected:\n{expected_example}"
        )
