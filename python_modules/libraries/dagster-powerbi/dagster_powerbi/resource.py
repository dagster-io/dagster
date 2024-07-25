from typing import Any, Dict

import requests
from dagster import ConfigurableResource
from dagster._utils.cached_method import cached_method
from pydantic import Field

BASE_API_URL = "https://api.powerbi.com/v1.0/myorg/"


class PowerBIResource(ConfigurableResource):
    """A resource used to interact with the PowerBI API."""

    api_token: str = Field(..., description="An API token used to connect to PowerBI.")
    workspace_id: str = Field(..., description="The ID of the PowerBI group to use.")

    def fetch_json(self, endpoint: str) -> Dict[str, Any]:
        """Fetch JSON data from the PowerBI API. Raises an exception if the request fails.

        Args:
            endpoint (str): The API endpoint to fetch data from.

        Returns:
            Dict[str, Any]: The JSON data returned from the API.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }
        response = requests.get(
            f"{BASE_API_URL}/groups/{self.workspace_id}/{endpoint}", headers=headers
        )
        response.raise_for_status()
        return response.json()

    @cached_method
    def get_reports(self) -> Dict[str, Any]:
        """Fetches a list of all PowerBI reports in the workspace."""
        return self.fetch_json("reports")

    @cached_method
    def get_semantic_models(self) -> Dict[str, Any]:
        """Fetches a list of all PowerBI semantic models in the workspace."""
        return self.fetch_json("datasets")

    @cached_method
    def get_semantic_model_sources(
        self,
        dataset_id: str,
    ) -> Dict[str, Any]:
        """Fetches a list of all data sources for a given semantic model."""
        return self.fetch_json(f"datasets/{dataset_id}/datasources")

    @cached_method
    def get_dashboards(self) -> Dict[str, Any]:
        """Fetches a list of all PowerBI dashboards in the workspace."""
        return self.fetch_json("dashboards")

    @cached_method
    def get_dashboard_tiles(
        self,
        dashboard_id: str,
    ) -> Dict[str, Any]:
        """Fetches a list of all tiles for a given PowerBI dashboard,
        including which reports back each tile.
        """
        return self.fetch_json(f"dashboards/{dashboard_id}/tiles")
