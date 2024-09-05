from abc import abstractmethod
from typing import Any, Dict, Optional

import requests
from dagster import ConfigurableResource, InitResourceContext
from dagster._utils.cached_method import cached_method
from pydantic import Field, PrivateAttr

TABLEAU_API_VERSION = "3.23"


class BaseTableauWorkspace(ConfigurableResource):
    """Base class to represent a workspace in Tableau and provides utilities
    to interact with the Tableau API.
    """

    personal_access_token_name: str = Field(
        ..., description="The name of the personal access token used to connect to Tableau API."
    )
    personal_access_token_value: str = Field(
        ..., description="The value of the personal access token used to connect to Tableau API."
    )
    site_id: str = Field(..., description="The ID of the Tableau site to use.")

    _api_token: Optional[str] = PrivateAttr(default=None)

    def setup_for_execution(self, context: InitResourceContext) -> None:
        # Sign in and refresh access token when the resource is initialized
        response = self.sign_in()
        self._api_token = response["credentials"]["token"]

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        # Sign out after execution
        self.sign_out()
        self._api_token = None

    @property
    @abstractmethod
    def api_base_url(self) -> str:
        raise NotImplementedError()

    def fetch_json(
        self,
        endpoint: str,
        headers: Dict[str, Any],
        data: Optional[Dict[str, Any]] = None,
        method: str = "GET",
    ) -> Dict[str, Any]:
        """Fetch JSON data from the Tableau API. Raises an exception if the request fails.

        Args:
            endpoint (str): The API endpoint to fetch data from.
            headers (Dict[str, Any]): Dictionary of HTTP Headers to send with the request.
            data (Optional[Dict[str, Any]]): JSON-formatted data string to be included in the request.
            method (str): The HTTP method to use for the request.

        Returns:
            Dict[str, Any]: The JSON data returned from the API.
        """
        request_args: Dict[str, Any] = dict(
            method=method,
            url=f"{self.api_base_url}/{endpoint}",
            headers=headers,
        )
        if data:
            request_args["json"] = data
        response = requests.request(**request_args)
        response.raise_for_status()
        return response.json()

    def fetch_json_with_token(self, endpoint: str, method: str = "GET") -> Dict[str, Any]:
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "X-tableau-auth": self._api_token,
        }
        return self.fetch_json(endpoint=endpoint, headers=headers, method=method)

    @cached_method
    def get_workbooks(self) -> Dict[str, Any]:
        """Fetches a list of all Tableau workbooks in the workspace."""
        return self.fetch_json_with_token(self.with_site_id("workbooks"))

    @cached_method
    def get_workbook_data_sources(
        self,
        workbook_id: str,
    ) -> Dict[str, Any]:
        """Fetches a list of all data sources for a given workbook."""
        return self.fetch_json_with_token(self.with_site_id(f"workbooks/{workbook_id}/connections"))

    def sign_in(self):
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
        }
        data = {
            "credentials": {
                "personalAccessTokenName": self.personal_access_token_name,
                "personalAccessTokenSecret": self.personal_access_token_value,
                "site": {"contentUrl": self.site_id},
            }
        }
        return self.fetch_json(endpoint="auth/signin", headers=headers, data=data, method="POST")

    def sign_out(self):
        return self.fetch_json_with_token(endpoint="auth/signout", method="POST")

    def with_site_id(self, endpoint: str):
        return f"sites/{self.site_id}/{endpoint}"


class TableauCloudWorkspace(BaseTableauWorkspace):
    """Represents a workspace in Tableau Cloud and provides utilities
    to interact with the Tableau API.
    """

    pod_name: str = Field(..., description="The pod name of the Tableau Cloud workspace.")

    @property
    def api_base_url(self) -> str:
        return f"https://{self.pod_name}.online.tableau.com/api/{TABLEAU_API_VERSION}"


class TableauServerWorkspace(BaseTableauWorkspace):
    """Represents a workspace in Tableau Server and provides utilities
    to interact with the Tableau API.
    """

    server_name: str = Field(..., description="The server name of the Tableau Server workspace.")

    @property
    def api_base_url(self) -> str:
        return f"https://{self.server_name}/api/{TABLEAU_API_VERSION}"
