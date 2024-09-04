from typing import Any, Dict, Optional

import requests
from dagster import ConfigurableResource, InitResourceContext
from dagster._utils.cached_method import cached_method
from pydantic import Field, PrivateAttr

TABLEAU_API_VERSION = "3.23"


class TableauWorkspace(ConfigurableResource):
    """Represents a workspace in Tableau and provides utilities
    to interact with the Tableau API.
    """

    host: str = Field(..., description="The host of the Tableau workspace.")
    personal_access_token_name: str = Field(
        ..., description="The name of the personal access token used to connect to Tableau API."
    )
    personal_access_token_value: str = Field(
        ..., description="The value of the personal access token used to connect to Tableau API."
    )
    site_id: str = Field(..., description="The ID of the Tableau site to use.")

    _access_token: Optional[str] = PrivateAttr(default=None)

    def setup_for_execution(self, context: InitResourceContext) -> None:
        # Sign in and refresh access token when the resource is initialized
        response = self.sign_in()
        self._access_token = response["credentials"]["token"]

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        # Sign out after execution
        self.sign_out()
        self._access_token = None

    @property
    def api_base_url(self) -> str:
        return f"https://{self.host}/api/{TABLEAU_API_VERSION}"

    def fetch_json(self, endpoint: str) -> Dict[str, Any]:
        """Fetch JSON data from the PowerBI API. Raises an exception if the request fails.

        Args:
            endpoint (str): The API endpoint to fetch data from.

        Returns:
            Dict[str, Any]: The JSON data returned from the API.
        """
        # TODO: handle headers for sign in
        headers = {"X-tableau-auth": self._access_token}
        response = requests.get(f"{self.api_base_url}/{endpoint}", headers=headers)
        response.raise_for_status()
        return response.json()

    @cached_method
    def get_workbooks(self) -> Dict[str, Any]:
        """Fetches a list of all Tableau workbooks in the workspace."""
        return self.fetch_json(self.with_site_id("workbooks"))

    @cached_method
    def get_workbook_data_sources(
        self,
        workbook_id: str,
    ) -> Dict[str, Any]:
        """Fetches a list of all data sources for a given workbook."""
        return self.fetch_json(self.with_site_id(f"workbooks/{workbook_id}/connections"))

    def sign_in(self):
        return self.fetch_json("auth/signin")

    def sign_out(self):
        return self.fetch_json("auth/signout")

    def with_site_id(self, endpoint: str):
        return f"sites/{self.site_id}/{endpoint}"
