"""Test code location business logic functions without mocks."""

import json
import os
import tempfile

from dagster_dg_cli.api_layer.graphql_adapter.code_location import (
    process_add_location_response,
    process_code_locations_response,
    process_delete_location_response,
)
from dagster_dg_cli.api_layer.schemas.code_location import (
    DgApiAddCodeLocationResult,
    DgApiCodeLocation,
    DgApiCodeLocationDocument,
    DgApiCodeLocationList,
    DgApiCodeSource,
    DgApiDeleteCodeLocationResult,
    DgApiGitMetadata,
)
from dagster_dg_cli.cli.api.code_location import build_code_location_document
from dagster_dg_cli.cli.api.formatters import (
    format_add_code_location_result,
    format_code_location,
    format_code_locations,
    format_delete_code_location_result,
)


class TestProcessAddLocationResponse:
    """Test the pure functions that process GraphQL responses."""

    def test_process_add_location_response_success(self):
        response = {
            "__typename": "WorkspaceEntry",
            "locationName": "my-location",
        }
        result = process_add_location_response(response)
        assert isinstance(result, DgApiAddCodeLocationResult)
        assert result.location_name == "my-location"

    def test_process_add_location_response_invalid(self):
        response = {
            "__typename": "InvalidLocationError",
            "errors": ["Missing image", "Invalid module"],
        }
        try:
            process_add_location_response(response)
            assert False, "Should have raised"
        except ValueError as e:
            assert "Invalid location config" in str(e)
            assert "Missing image" in str(e)
            assert "Invalid module" in str(e)

    def test_process_add_location_response_python_error(self):
        response = {
            "__typename": "PythonError",
            "message": "Internal server error",
            "stack": ["traceback line 1"],
        }
        try:
            process_add_location_response(response)
            assert False, "Should have raised"
        except ValueError as e:
            assert "Internal server error" in str(e)

    def test_process_add_location_response_unauthorized(self):
        response = {
            "__typename": "UnauthorizedError",
            "message": "Not authorized",
        }
        try:
            process_add_location_response(response)
            assert False, "Should have raised"
        except ValueError as e:
            assert "Not authorized" in str(e)


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


class TestDocumentToDict:
    """Test document serialization."""

    def test_document_to_dict_strips_nones(self):
        doc = DgApiCodeLocationDocument(
            location_name="my-loc",
            image="my-image:latest",
            code_source=DgApiCodeSource(module_name="my_module"),
        )
        d = doc.to_document_dict()
        assert d == {
            "location_name": "my-loc",
            "image": "my-image:latest",
            "code_source": {"module_name": "my_module"},
        }
        # Verify no None values at any level
        assert "git" not in d
        assert "working_directory" not in d
        assert "python_file" not in d.get("code_source", {})

    def test_document_to_dict_full(self):
        doc = DgApiCodeLocationDocument(
            location_name="my-loc",
            image="my-image:latest",
            code_source=DgApiCodeSource(module_name="my_module", python_file="main.py"),
            working_directory="/opt",
            git=DgApiGitMetadata(commit_hash="abc123"),
        )
        d = doc.to_document_dict()
        assert d["location_name"] == "my-loc"
        assert d["code_source"]["module_name"] == "my_module"
        assert d["code_source"]["python_file"] == "main.py"
        assert d["git"]["commit_hash"] == "abc123"
        assert "url" not in d["git"]


class TestFormatResult:
    """Test the formatter functions."""

    def test_format_result_text(self):
        result = DgApiAddCodeLocationResult(location_name="my-loc")
        output = format_add_code_location_result(result, as_json=False)
        assert output == "Added or updated code location 'my-loc'."

    def test_format_result_json(self):
        result = DgApiAddCodeLocationResult(location_name="my-loc")
        output = format_add_code_location_result(result, as_json=True)
        parsed = json.loads(output)
        assert parsed["location_name"] == "my-loc"


class TestProcessCodeLocationsResponse:
    """Test the pure function that processes workspace entries."""

    def test_process_code_locations_response_success(self):
        response = {
            "workspace": {
                "workspaceEntries": [
                    {
                        "locationName": "loc-a",
                        "serializedDeploymentMetadata": json.dumps(
                            {"image": "img-a:latest", "module_name": "mod_a"}
                        ),
                    },
                    {
                        "locationName": "loc-b",
                        "serializedDeploymentMetadata": json.dumps(
                            {"image": "img-b:v2", "python_file": "defs.py"}
                        ),
                    },
                ]
            }
        }
        result = process_code_locations_response(response)
        assert isinstance(result, DgApiCodeLocationList)
        assert result.total == 2
        assert result.items[0].location_name == "loc-a"
        assert result.items[0].image == "img-a:latest"
        assert result.items[0].code_source is not None
        assert result.items[0].code_source.module_name == "mod_a"
        assert result.items[1].location_name == "loc-b"
        assert result.items[1].image == "img-b:v2"
        assert result.items[1].code_source is not None
        assert result.items[1].code_source.python_file == "defs.py"

    def test_process_code_locations_response_empty(self):
        response = {"workspace": {"workspaceEntries": []}}
        result = process_code_locations_response(response)
        assert isinstance(result, DgApiCodeLocationList)
        assert result.total == 0
        assert result.items == []

    def test_process_code_locations_response_no_metadata(self):
        response = {
            "workspace": {
                "workspaceEntries": [
                    {
                        "locationName": "loc-bare",
                        "serializedDeploymentMetadata": None,
                    },
                ]
            }
        }
        result = process_code_locations_response(response)
        assert result.total == 1
        assert result.items[0].location_name == "loc-bare"
        assert result.items[0].image is None
        assert result.items[0].code_source is None


class TestFormatCodeLocations:
    """Test code location formatters."""

    def test_format_code_locations_text(self):
        locations = DgApiCodeLocationList(
            items=[
                DgApiCodeLocation(location_name="loc-a", image="img-a:latest"),
                DgApiCodeLocation(location_name="loc-b", image="img-b:v2"),
            ],
            total=2,
        )
        output = format_code_locations(locations, as_json=False)
        assert "loc-a" in output
        assert "img-a:latest" in output
        assert "loc-b" in output
        assert "NAME" in output
        assert "IMAGE" in output

    def test_format_code_locations_json(self):
        locations = DgApiCodeLocationList(
            items=[
                DgApiCodeLocation(location_name="loc-a", image="img-a:latest"),
            ],
            total=1,
        )
        output = format_code_locations(locations, as_json=True)
        parsed = json.loads(output)
        assert parsed["total"] == 1
        assert parsed["items"][0]["location_name"] == "loc-a"

    def test_format_code_location_text(self):
        location = DgApiCodeLocation(
            location_name="my-loc",
            image="my-image:latest",
            code_source=DgApiCodeSource(module_name="my_mod"),
        )
        output = format_code_location(location, as_json=False)
        assert "my-loc" in output
        assert "my-image:latest" in output
        assert "my_mod" in output

    def test_format_code_location_json(self):
        location = DgApiCodeLocation(
            location_name="my-loc",
            image="my-image:latest",
        )
        output = format_code_location(location, as_json=True)
        parsed = json.loads(output)
        assert parsed["location_name"] == "my-loc"
        assert parsed["image"] == "my-image:latest"


class TestProcessDeleteLocationResponse:
    """Test the pure function that processes delete location GraphQL responses."""

    def test_process_delete_location_response_success(self):
        response = {
            "__typename": "DeleteLocationSuccess",
            "locationName": "my-location",
        }
        result = process_delete_location_response(response)
        assert isinstance(result, DgApiDeleteCodeLocationResult)
        assert result.location_name == "my-location"

    def test_process_delete_location_response_python_error(self):
        response = {
            "__typename": "PythonError",
            "message": "Internal server error",
            "stack": ["traceback line 1"],
        }
        try:
            process_delete_location_response(response)
            assert False, "Should have raised"
        except ValueError as e:
            assert "Internal server error" in str(e)

    def test_process_delete_location_response_unauthorized(self):
        response = {
            "__typename": "UnauthorizedError",
            "message": "Not authorized",
        }
        try:
            process_delete_location_response(response)
            assert False, "Should have raised"
        except ValueError as e:
            assert "Not authorized" in str(e)


class TestFormatDeleteCodeLocationResult:
    """Test the delete code location formatter."""

    def test_format_delete_code_location_result_text(self):
        result = DgApiDeleteCodeLocationResult(location_name="my-loc")
        output = format_delete_code_location_result(result, as_json=False)
        assert output == "Deleted code location 'my-loc'."

    def test_format_delete_code_location_result_json(self):
        result = DgApiDeleteCodeLocationResult(location_name="my-loc")
        output = format_delete_code_location_result(result, as_json=True)
        parsed = json.loads(output)
        assert parsed["location_name"] == "my-loc"
