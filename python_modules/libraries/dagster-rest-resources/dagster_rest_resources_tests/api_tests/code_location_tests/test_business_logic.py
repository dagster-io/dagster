"""Test code location business logic functions without mocks."""

import json
from unittest.mock import MagicMock

from dagster_rest_resources.graphql_adapter.code_location import (
    get_code_location_via_graphql,
    process_add_location_response,
    process_code_locations_response,
    process_delete_location_response,
)
from dagster_rest_resources.schemas.code_location import (
    DgApiAddCodeLocationResult,
    DgApiCodeLocationDocument,
    DgApiCodeLocationList,
    DgApiCodeSource,
    DgApiDeleteCodeLocationResult,
    DgApiGitMetadata,
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


class TestGetCodeLocationViaGraphql:
    """Test the get_code_location_via_graphql function."""

    def _make_client(self, entries: list[dict], statuses: list[dict] | None = None):
        """Create a fake GraphQL client that returns workspace entries and location statuses."""
        workspace_response = {"workspace": {"workspaceEntries": entries}}
        statuses_response = {
            "locationStatusesOrError": {
                "__typename": "WorkspaceLocationStatusEntries",
                "entries": statuses or [],
            }
        }

        client = MagicMock()
        client.execute.side_effect = [workspace_response, statuses_response]
        return client

    def test_get_code_location_via_graphql_found(self):
        entries = [
            {
                "locationName": "loc-a",
                "serializedDeploymentMetadata": json.dumps(
                    {"image": "img-a:latest", "module_name": "mod_a"}
                ),
            },
            {
                "locationName": "loc-b",
                "serializedDeploymentMetadata": json.dumps({"image": "img-b:v2"}),
            },
        ]
        statuses = [
            {"name": "loc-a", "loadStatus": "LOADED"},
            {"name": "loc-b", "loadStatus": "LOADED"},
        ]
        client = self._make_client(entries, statuses)
        result = get_code_location_via_graphql(client, "loc-b")
        assert result is not None
        assert result.location_name == "loc-b"
        assert result.image == "img-b:v2"
        assert result.status == "LOADED"

    def test_get_code_location_via_graphql_not_found(self):
        entries = [
            {
                "locationName": "loc-a",
                "serializedDeploymentMetadata": json.dumps({"image": "img-a:latest"}),
            },
        ]
        client = self._make_client(entries)
        result = get_code_location_via_graphql(client, "nonexistent")
        assert result is None
