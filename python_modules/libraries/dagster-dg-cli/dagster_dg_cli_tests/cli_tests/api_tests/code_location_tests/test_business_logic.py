"""Test code location business logic functions without mocks."""

from dagster_dg_cli.api_layer.graphql_adapter.code_location import process_delete_location_response

from dagster_dg_cli_tests.cli_tests.api_tests.test_dynamic_command_execution import (
    ReplayClient,
    load_recorded_graphql_responses,
)


class TestProcessDeleteCodeLocationResponse:
    """Test the pure function that processes delete code location GraphQL responses."""

    def test_successful_response_processing(self, snapshot):
        """Test processing a successful delete code location response."""
        response = load_recorded_graphql_responses("code_location", "success_delete_code_location")[
            0
        ]
        location_data = response.get("deleteLocation", {})
        result = process_delete_location_response(location_data)

        snapshot.assert_match(result)


class TestDeleteCodeLocationViaApi:
    """Test that the API layer correctly delegates to the GraphQL adapter."""

    def test_delete_code_location(self):
        """Test deleting a code location via the API layer."""
        from dagster_dg_cli.api_layer.api.code_locations import DgApiCodeLocationApi

        response = {
            "deleteLocation": {
                "__typename": "DeleteLocationSuccess",
                "locationName": "my-location",
            }
        }
        client = ReplayClient([response])
        api = DgApiCodeLocationApi(client)

        result = api.delete_code_location("my-location")
        assert result.location_name == "my-location"
