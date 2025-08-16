import json
from pathlib import Path

from dagster_dg_core.yaml_template.converter import YamlTemplate


class TestComplexDbtProjectSchema:
    def test_dbt_project_component_model_schema(self):
        """Test the complex DbtProjectComponentModel schema provided by user."""
        # Load schema from external file
        test_data_dir = Path(__file__).parent / "test_data" / "dbt_project_component_model"
        schema_file = test_data_dir / "schema.json"

        with open(schema_file) as f:
            schema = json.load(f)

        # Generate YAML template
        template = YamlTemplate.from_json_schema(schema)
        result = template.to_string()

        # Verify the template was generated without errors
        assert isinstance(result, str)
        assert len(result) > 0

        # Verify it contains the expected sections
        assert "# Template with instructions" in result
        assert "# EXAMPLE VALUES:" in result

        # Verify it contains some key properties
        assert "project:" in result  # Required field
        assert "Required" in result  # Should have required field comments
        assert "Optional" in result  # Should have optional field comments

        # Verify it handles complex nested structures
        assert "anyOf" not in result  # Should not leak schema internals
        assert "$ref" not in result  # Should not leak schema internals
        assert "$defs" not in result  # Should not leak schema internals

        # The template was generated without errors - we could print here if needed for manual inspection

        # The template should be reasonably sized (not empty, not excessively long)
        lines = result.split("\n")
        assert len(lines) > 10  # Should have substantial content
        assert len(lines) < 200  # But not be overwhelming

        # Verify some specific expected content
        assert "project: " in result
        assert '"example_string"' in result or '"' in result  # Should have example values

    def test_handles_unsupported_json_schema_features_gracefully(self):
        """Test that unsupported JSON Schema features are handled gracefully."""
        schema = {
            "type": "object",
            "properties": {
                "unsupported_feature": {"anyOf": [{"type": "string"}, {"type": "number"}]},
                "normal_property": {"type": "string"},
            },
        }

        template = YamlTemplate.from_json_schema(schema)
        result = template.to_string()

        # Should still generate a template, even if it can't handle all features perfectly
        assert "# Template with instructions" in result
        assert "normal_property:" in result
        assert "# EXAMPLE VALUES:" in result
