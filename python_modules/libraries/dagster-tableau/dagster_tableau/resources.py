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
    site_name: str = Field(..., description="The name of the Tableau site to use.")

    _api_token: Optional[str] = PrivateAttr(default=None)
    _site_id: Optional[str] = PrivateAttr(default=None)

    def setup_for_execution(self, context: InitResourceContext) -> None:
        # Sign in and refresh access token when the resource is initialized
        response = self.sign_in()
        self._api_token = response["credentials"]["token"]
        self._site_id = response["credentials"]["site"]["id"]

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        # Sign out after execution
        self.sign_out()
        self._api_token = None
        self._site_id = None

    @property
    @abstractmethod
    def api_base_url(self) -> str:
        raise NotImplementedError()

    def _fetch_json(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        with_auth_header: bool = True,
    ) -> Dict[str, Any]:
        """Fetch JSON data from the Tableau API. Raises an exception if the request fails.

        Args:
            endpoint (str): The API endpoint to fetch data from.
            data (Optional[Dict[str, Any]]): JSON-formatted data string to be included in the request.
            method (str): The HTTP method to use for the request.
            with_auth_header (bool): Whether to add X-Tableau-Auth header to the request. Enabled by default.

        Returns:
            Dict[str, Any]: The JSON data returned from the API.
        """
        response = self._make_request(
            endpoint=endpoint, data=data, method=method, with_auth_header=with_auth_header
        )
        return response.json()

    def _make_request(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        with_auth_header: bool = True,
    ) -> requests.Response:
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
        }
        if with_auth_header:
            headers["X-tableau-auth"] = self._api_token
        request_args: Dict[str, Any] = dict(
            method=method,
            url=f"{self.api_base_url}/{endpoint}",
            headers=headers,
        )
        if data:
            request_args["json"] = data
        response = requests.request(**request_args)
        response.raise_for_status()
        return response

    @cached_method
    def get_workbooks(self) -> Dict[str, Any]:
        """Fetches a list of all Tableau workbooks in the workspace."""
        return self._fetch_json(self._with_site_id("workbooks"))

    @cached_method
    def get_workbook(self, workbook_id) -> Dict[str, Any]:
        """Fetches information, including views and tags, for a given workbook."""
        return self._fetch_json(self._with_site_id(f"workbooks/{workbook_id}"))

    @cached_method
    def get_workbook_data_sources(
        self,
        workbook_id: str,
    ) -> Dict[str, Any]:
        """Fetches a list of all data sources for a given workbook."""
        return self._fetch_json(self._with_site_id(f"workbooks/{workbook_id}/connections"))

    def sign_in(self):
        """Sign in to the site in Tableau."""
        data = {
            "credentials": {
                "personalAccessTokenName": self.personal_access_token_name,
                "personalAccessTokenSecret": self.personal_access_token_value,
                "site": {"contentUrl": self.site_name},
            }
        }
        return self._fetch_json(
            endpoint="auth/signin", data=data, method="POST", with_auth_header=False
        )

    def sign_out(self):
        """Sign out from the site in Tableau."""
        return self._make_request(endpoint="auth/signout", method="POST")

    def _with_site_id(self, endpoint: str):
        return f"sites/{self._site_id}/{endpoint}"


class TableauCloudWorkspace(BaseTableauWorkspace):
    """Represents a workspace in Tableau Cloud and provides utilities
    to interact with the Tableau API.
    """

    pod_name: str = Field(..., description="The pod name of the Tableau Cloud workspace.")

    @property
    def api_base_url(self) -> str:
        """API base URL for Tableau Cloud."""
        return f"https://{self.pod_name}.online.tableau.com/api/{TABLEAU_API_VERSION}"


class TableauServerWorkspace(BaseTableauWorkspace):
    """Represents a workspace in Tableau Server and provides utilities
    to interact with the Tableau API.
    """

    server_name: str = Field(..., description="The server name of the Tableau Server workspace.")

    @property
    def api_base_url(self) -> str:
        """API base URL for Tableau Server."""
        return f"https://{self.server_name}/api/{TABLEAU_API_VERSION}"
