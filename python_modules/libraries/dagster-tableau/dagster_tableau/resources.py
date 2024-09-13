from abc import abstractmethod
from contextlib import contextmanager
from typing import Mapping, Optional, Union

import requests
from dagster import ConfigurableResource, InitResourceContext
from dagster._utils.cached_method import cached_method
from pydantic import Field, PrivateAttr

TABLEAU_API_VERSION = "3.23"


class BaseTableauClient:
    def __init__(
        self, personal_access_token_name: str, personal_access_token_value: str, site_name: str
    ):
        self.personal_access_token_name = personal_access_token_name
        self.personal_access_token_value = personal_access_token_value
        self.site_name = site_name
        self._api_token = None
        self._site_id = None

    @property
    @abstractmethod
    def rest_api_base_url(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def metadata_api_base_url(self) -> str:
        raise NotImplementedError()

    def _fetch_json(
        self,
        endpoint: str,
        data: Optional[Mapping[str, object]] = None,
        method: str = "GET",
        with_auth_header: bool = True,
    ) -> Mapping[str, object]:
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
        data: Optional[Mapping[str, object]] = None,
        method: str = "GET",
        with_auth_header: bool = True,
    ) -> requests.Response:
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
        }
        if with_auth_header:
            headers["X-tableau-auth"] = self._api_token
        request_args = dict(
            method=method,
            url=f"{self.rest_api_base_url}/{endpoint}",
            headers=headers,
        )
        if data:
            request_args["json"] = data
        response = requests.request(**request_args)
        response.raise_for_status()
        return response

    @cached_method
    def get_workbooks(self) -> Mapping[str, object]:
        """Fetches a list of all Tableau workbooks in the workspace."""
        return self._fetch_json(self._with_site_id("workbooks"))

    @cached_method
    def get_workbook(self, workbook_id) -> Mapping[str, object]:
        """Fetches information, including views and tags, for a given workbook."""
        return self._fetch_json(self._with_site_id(f"workbooks/{workbook_id}"))

    @cached_method
    def get_workbook_data_sources(
        self,
        workbook_id: str,
    ) -> Mapping[str, object]:
        """Fetches a list of all Tableau data sources in the workspace."""
        return self._fetch_json(self._with_site_id(f"workbooks/{workbook_id}/connections"))

    def sign_in(self) -> Mapping[str, object]:
        """Sign in to the site in Tableau."""
        data = {
            "credentials": {
                "personalAccessTokenName": self.personal_access_token_name,
                "personalAccessTokenSecret": self.personal_access_token_value,
                "site": {"contentUrl": self.site_name},
            }
        }
        response = self._fetch_json(
            endpoint="auth/signin", data=data, method="POST", with_auth_header=False
        )
        self._api_token = response["credentials"]["token"]
        self._site_id = response["credentials"]["site"]["id"]
        return response

    def sign_out(self) -> None:
        """Sign out from the site in Tableau."""
        self._make_request(endpoint="auth/signout", method="POST")
        self._api_token = None
        self._site_id = None

    def _with_site_id(self, endpoint: str) -> str:
        return f"sites/{self._site_id}/{endpoint}"


class TableauCloudClient(BaseTableauClient):
    """Represents a client for Tableau Cloud and provides utilities
    to interact with the Tableau API.
    """

    def __init__(
        self,
        personal_access_token_name: str,
        personal_access_token_value: str,
        site_name: str,
        pod_name: str,
    ):
        self.pod_name = pod_name
        super().__init__(
            personal_access_token_name=personal_access_token_name,
            personal_access_token_value=personal_access_token_value,
            site_name=site_name,
        )

    @property
    def rest_api_base_url(self) -> str:
        """REST API base URL for Tableau Cloud."""
        return f"https://{self.pod_name}.online.tableau.com/api/{TABLEAU_API_VERSION}"

    @property
    def metadata_api_base_url(self) -> str:
        """Metadata API base URL for Tableau Cloud."""
        return f"https://{self.pod_name}.online.tableau.com/api/metadata/graphql"


class TableauServerClient(BaseTableauClient):
    """Represents a client for Tableau Server and provides utilities
    to interact with Tableau APIs.
    """

    def __init__(
        self,
        personal_access_token_name: str,
        personal_access_token_value: str,
        site_name: str,
        server_name: str,
    ):
        self.server_name = server_name
        super().__init__(
            personal_access_token_name=personal_access_token_name,
            personal_access_token_value=personal_access_token_value,
            site_name=site_name,
        )

    @property
    def rest_api_base_url(self) -> str:
        """REST API base URL for Tableau Server."""
        return f"https://{self.server_name}/api/{TABLEAU_API_VERSION}"

    @property
    def metadata_api_base_url(self) -> str:
        """Metadata API base URL for Tableau Server."""
        return f"https://{self.server_name}/api/metadata/graphql"


class BaseTableauWorkspace(ConfigurableResource):
    """Base class to represent a workspace in Tableau and provides utilities
    to interact with Tableau APIs.
    """

    personal_access_token_name: str = Field(
        ..., description="The name of the personal access token used to connect to Tableau APIs."
    )
    personal_access_token_value: str = Field(
        ..., description="The value of the personal access token used to connect to Tableau APIs."
    )
    site_name: str = Field(..., description="The name of the Tableau site to use.")

    _client: Union[TableauCloudClient, TableauServerClient] = PrivateAttr(default=None)

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self.build_client()

    @abstractmethod
    def build_client(self) -> None:
        raise NotImplementedError()

    @contextmanager
    def get_client(self):
        if not self._client:
            self.build_client()
        self._client.sign_in()
        yield self._client
        self._client.sign_out()


class TableauCloudWorkspace(BaseTableauWorkspace):
    """Represents a workspace in Tableau Cloud and provides utilities
    to interact with Tableau APIs.
    """

    pod_name: str = Field(..., description="The pod name of the Tableau Cloud workspace.")

    def build_client(self) -> None:
        self._client = TableauCloudClient(
            personal_access_token_name=self.personal_access_token_name,
            personal_access_token_value=self.personal_access_token_value,
            site_name=self.site_name,
            pod_name=self.pod_name,
        )


class TableauServerWorkspace(BaseTableauWorkspace):
    """Represents a workspace in Tableau Server and provides utilities
    to interact with Tableau APIs.
    """

    server_name: str = Field(..., description="The server name of the Tableau Server workspace.")

    def build_client(self) -> None:
        self._client = TableauServerClient(
            personal_access_token_name=self.personal_access_token_name,
            personal_access_token_value=self.personal_access_token_value,
            site_name=self.site_name,
            server_name=self.server_name,
        )
