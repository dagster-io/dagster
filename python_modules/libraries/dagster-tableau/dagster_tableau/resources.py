import datetime
import uuid
from abc import abstractmethod
from contextlib import contextmanager
from typing import Mapping, Optional, Union

import jwt
import requests
from dagster._annotations import experimental
from dagster import ConfigurableResource, InitResourceContext
from dagster._utils.cached_method import cached_method
from pydantic import Field, PrivateAttr

TABLEAU_REST_API_VERSION = "3.23"


@experimental
class BaseTableauClient:
    def __init__(
        self,
        connected_app_client_id: str,
        connected_app_secret_id: str,
        connected_app_secret_value: str,
        username: str,
        site_name: str,
    ):
        self.connected_app_client_id = connected_app_client_id
        self.connected_app_secret_id = connected_app_secret_id
        self.connected_app_secret_value = connected_app_secret_value
        self.username = username
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
        url: str,
        data: Optional[Mapping[str, object]] = None,
        method: str = "GET",
        with_auth_header: bool = True,
    ) -> Mapping[str, object]:
        """Fetch JSON data from the Tableau APIs given the URL. Raises an exception if the request fails.

        Args:
            url (str): The url to fetch data from.
            data (Optional[Dict[str, Any]]): JSON-formatted data string to be included in the request.
            method (str): The HTTP method to use for the request.
            with_auth_header (bool): Whether to add X-Tableau-Auth header to the request. Enabled by default.

        Returns:
            Dict[str, Any]: The JSON data returned from the API.
        """
        response = self._make_request(
            url=url, data=data, method=method, with_auth_header=with_auth_header
        )
        return response.json()

    def _make_request(
        self,
        url: str,
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
            url=url,
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
        endpoint = self._with_site_id("workbooks")
        return self._fetch_json(url=f"{self.rest_api_base_url}/{endpoint}")

    @cached_method
    def get_workbook(self, workbook_id) -> Mapping[str, object]:
        """Fetches information, including sheets, dashboards and data sources, for a given workbook."""
        data = {"query": self.workbook_graphql_query, "variables": {"luid": workbook_id}}
        return self._fetch_json(url=self.metadata_api_base_url, data=data, method="POST")

    def sign_in(self) -> Mapping[str, object]:
        """Sign in to the site in Tableau."""
        jwt_token = jwt.encode(
            {
                "iss": self.connected_app_client_id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
                "jti": str(uuid.uuid4()),
                "aud": "tableau",
                "sub": self.username,
                "scp": ["tableau:content:read"],
            },
            self.connected_app_secret_value,
            algorithm="HS256",
            headers={"kid": self.connected_app_secret_id, "iss": self.connected_app_client_id},
        )
        data = {
            "credentials": {
                "jwt": jwt_token,
                "site": {"contentUrl": self.site_name},
            }
        }
        response = self._fetch_json(
            url=f"{self.rest_api_base_url}/auth/signin",
            data=data,
            method="POST",
            with_auth_header=False,
        )
        self._api_token = response["credentials"]["token"]
        self._site_id = response["credentials"]["site"]["id"]
        return response

    def sign_out(self) -> None:
        """Sign out from the site in Tableau."""
        self._make_request(url=f"{self.rest_api_base_url}/auth/signout", method="POST")
        self._api_token = None
        self._site_id = None

    def _with_site_id(self, endpoint: str) -> str:
        return f"sites/{self._site_id}/{endpoint}"

    @property
    def workbook_graphql_query(self) -> str:
        return """
            query workbooks($luid: String!) { 
              workbooks(filter: {luid: $luid}) {
                id
                luid
                name
                sheets {
                  id
                  luid
                  name
                  parentEmbeddedDatasources {
                    id
                    name
                  }
                }
                dashboards {
                  id
                  luid
                  name
                  sheets {
                    luid
                  }
                }
              }
            }
        """


@experimental
class TableauCloudClient(BaseTableauClient):
    """Represents a client for Tableau Cloud and provides utilities
    to interact with the Tableau API.
    """

    def __init__(
        self,
        connected_app_client_id: str,
        connected_app_secret_id: str,
        connected_app_secret_value: str,
        username: str,
        site_name: str,
        pod_name: str,
    ):
        self.pod_name = pod_name
        super().__init__(
            connected_app_client_id=connected_app_client_id,
            connected_app_secret_id=connected_app_secret_id,
            connected_app_secret_value=connected_app_secret_value,
            username=username,
            site_name=site_name,
        )

    @property
    def rest_api_base_url(self) -> str:
        """REST API base URL for Tableau Cloud."""
        return f"https://{self.pod_name}.online.tableau.com/api/{TABLEAU_REST_API_VERSION}"

    @property
    def metadata_api_base_url(self) -> str:
        """Metadata API base URL for Tableau Cloud."""
        return f"https://{self.pod_name}.online.tableau.com/api/metadata/graphql"


@experimental
class TableauServerClient(BaseTableauClient):
    """Represents a client for Tableau Server and provides utilities
    to interact with Tableau APIs.
    """

    def __init__(
        self,
        connected_app_client_id: str,
        connected_app_secret_id: str,
        connected_app_secret_value: str,
        username: str,
        site_name: str,
        server_name: str,
    ):
        self.server_name = server_name
        super().__init__(
            connected_app_client_id=connected_app_client_id,
            connected_app_secret_id=connected_app_secret_id,
            connected_app_secret_value=connected_app_secret_value,
            username=username,
            site_name=site_name,
        )

    @property
    def rest_api_base_url(self) -> str:
        """REST API base URL for Tableau Server."""
        return f"https://{self.server_name}/api/{TABLEAU_REST_API_VERSION}"

    @property
    def metadata_api_base_url(self) -> str:
        """Metadata API base URL for Tableau Server."""
        return f"https://{self.server_name}/api/metadata/graphql"


@experimental
class BaseTableauWorkspace(ConfigurableResource):
    """Base class to represent a workspace in Tableau and provides utilities
    to interact with Tableau APIs.
    """

    connected_app_client_id: str = Field(
        ..., description="The client id of the connected app used to connect to Tableau Workspace."
    )
    connected_app_secret_id: str = Field(
        ..., description="The secret id of the connected app used to connect to Tableau Workspace."
    )
    connected_app_secret_value: str = Field(
        ...,
        description="The secret value of the connected app used to connect to Tableau Workspace.",
    )
    username: str = Field(..., description="The username to authenticate to Tableau Workspace.")
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


@experimental
class TableauCloudWorkspace(BaseTableauWorkspace):
    """Represents a workspace in Tableau Cloud and provides utilities
    to interact with Tableau APIs.
    """

    pod_name: str = Field(..., description="The pod name of the Tableau Cloud workspace.")

    def build_client(self) -> None:
        self._client = TableauCloudClient(
            connected_app_client_id=self.connected_app_client_id,
            connected_app_secret_id=self.connected_app_secret_id,
            connected_app_secret_value=self.connected_app_secret_value,
            username=self.username,
            site_name=self.site_name,
            pod_name=self.pod_name,
        )


@experimental
class TableauServerWorkspace(BaseTableauWorkspace):
    """Represents a workspace in Tableau Server and provides utilities
    to interact with Tableau APIs.
    """

    server_name: str = Field(..., description="The server name of the Tableau Server workspace.")

    def build_client(self) -> None:
        self._client = TableauServerClient(
            connected_app_client_id=self.connected_app_client_id,
            connected_app_secret_id=self.connected_app_secret_id,
            connected_app_secret_value=self.connected_app_secret_value,
            username=self.username,
            site_name=self.site_name,
            server_name=self.server_name,
        )
