"""Test code location business logic functions without mocks."""

import json
import os
import tempfile

from dagster_dg_cli.cli.api.code_location import build_code_location_document
from dagster_dg_cli.cli.api.formatters import (
    format_add_code_location_result,
    format_code_location,
    format_code_locations,
    format_delete_code_location_result,
)
from dagster_rest_resources.schemas.code_location import (
    DgApiAddCodeLocationResult,
    DgApiCodeLocation,
    DgApiCodeLocationList,
    DgApiCodeSource,
    DgApiDeleteCodeLocationResult,
)


class TestBuildCodeLocationDocument:
    """Test the document building helper."""

    def test_build_document_basic(self):
        doc = build_code_location_document(
            location_name="my-loc",
            location_file=None,
            image="my-image:latest",
        )
        assert doc.location_name == "my-loc"
        assert doc.image == "my-image:latest"
        assert doc.code_source is None
        assert doc.git is None

    def test_build_document_with_code_source(self):
        doc = build_code_location_document(
            location_name="my-loc",
            location_file=None,
            module_name="my_module",
            package_name="my_package",
            python_file="my_file.py",
        )
        assert doc.code_source is not None
        assert doc.code_source.module_name == "my_module"
        assert doc.code_source.package_name == "my_package"
        assert doc.code_source.python_file == "my_file.py"

    def test_build_document_with_location_file(self):
        yaml_content = """
location_name: my-loc
image: file-image:v1
code_source:
  module_name: file_module
working_directory: /opt/dagster
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            try:
                doc = build_code_location_document(
                    location_name="my-loc",
                    location_file=f.name,
                )
                assert doc.location_name == "my-loc"
                assert doc.image == "file-image:v1"
                assert doc.code_source is not None
                assert doc.code_source.module_name == "file_module"
                assert doc.working_directory == "/opt/dagster"
            finally:
                os.unlink(f.name)

    def test_build_document_cli_overrides_file(self):
        yaml_content = """
location_name: my-loc
image: file-image:v1
code_source:
  module_name: file_module
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            try:
                doc = build_code_location_document(
                    location_name="my-loc",
                    location_file=f.name,
                    image="cli-image:v2",
                    module_name="cli_module",
                )
                assert doc.image == "cli-image:v2"
                assert doc.code_source is not None
                assert doc.code_source.module_name == "cli_module"
            finally:
                os.unlink(f.name)


class TestFormatResult:
    """Test the formatter functions."""

    def test_format_result_text(self, snapshot):
        result = DgApiAddCodeLocationResult(location_name="my-loc")
        output = format_add_code_location_result(result, as_json=False)
        assert output == "Added or updated code location 'my-loc'."
        snapshot.assert_match(output)

    def test_format_result_json(self, snapshot):
        result = DgApiAddCodeLocationResult(location_name="my-loc")
        output = format_add_code_location_result(result, as_json=True)
        parsed = json.loads(output)
        assert parsed["location_name"] == "my-loc"
        snapshot.assert_match(parsed)


class TestFormatCodeLocations:
    """Test code location formatters."""

    def test_format_code_locations_text(self, snapshot):
        locations = DgApiCodeLocationList(
            items=[
                DgApiCodeLocation(location_name="loc-a", image="img-a:latest", status="LOADED"),
                DgApiCodeLocation(location_name="loc-b", image="img-b:v2", status="LOADING"),
            ],
        )
        output = format_code_locations(locations, as_json=False)
        assert "loc-a" in output
        assert "img-a:latest" in output
        assert "loc-b" in output
        assert "NAME" in output
        assert "IMAGE" in output
        snapshot.assert_match(output)

    def test_format_code_locations_json(self, snapshot):
        locations = DgApiCodeLocationList(
            items=[
                DgApiCodeLocation(location_name="loc-a", image="img-a:latest", status="LOADED"),
            ],
        )
        output = format_code_locations(locations, as_json=True)
        parsed = json.loads(output)
        assert parsed["total"] == 1
        assert parsed["items"][0]["location_name"] == "loc-a"
        snapshot.assert_match(parsed)

    def test_format_code_location_text(self, snapshot):
        location = DgApiCodeLocation(
            location_name="my-loc",
            image="my-image:latest",
            code_source=DgApiCodeSource(module_name="my_mod"),
        )
        output = format_code_location(location, as_json=False)
        assert "my-loc" in output
        assert "my-image:latest" in output
        assert "my_mod" in output
        snapshot.assert_match(output)

    def test_format_code_location_json(self, snapshot):
        location = DgApiCodeLocation(
            location_name="my-loc",
            image="my-image:latest",
        )
        output = format_code_location(location, as_json=True)
        parsed = json.loads(output)
        assert parsed["location_name"] == "my-loc"
        assert parsed["image"] == "my-image:latest"
        snapshot.assert_match(parsed)


class TestFormatDeleteCodeLocationResult:
    """Test the delete code location formatter."""

    def test_format_delete_code_location_result_text(self, snapshot):
        result = DgApiDeleteCodeLocationResult(location_name="my-loc")
        output = format_delete_code_location_result(result, as_json=False)
        assert output == "Deleted code location 'my-loc'."
        snapshot.assert_match(output)

    def test_format_delete_code_location_result_json(self, snapshot):
        result = DgApiDeleteCodeLocationResult(location_name="my-loc")
        output = format_delete_code_location_result(result, as_json=True)
        parsed = json.loads(output)
        assert parsed["location_name"] == "my-loc"
        snapshot.assert_match(parsed)
